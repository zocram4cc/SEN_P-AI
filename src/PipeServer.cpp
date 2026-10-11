#include "PipeServer.h"
#include <algorithm>
#include <QFile>
#include <QCoreApplication>
#include <QNetworkReply>
#include <QRandomGenerator>


PipeServer::PipeServer(QObject *parent) : QObject(parent)
{
    server = new QLocalServer(this);
    connect(server,&QLocalServer::newConnection, this,&PipeServer::newConnection);
    server->setSocketOptions(QLocalServer::WorldAccessOption);
    server->listen("\\\\.\\pipe\\SEN_P-AI");
    if(!server->errorString().isEmpty())
        qDebug() << server->errorString();
    net = new QNetworkAccessManager(this);
    rigdioDisabled = QCoreApplication::arguments().contains("--no-rigdio");
}

static QString stripSlashes(QString s){
    while(s.startsWith('/')) s.remove(0,1);
    while(s.endsWith('/')) s.chop(1);
    return s;
}

static QString nameOf(const QJsonValue &player){ return player.toObject()["name"].toString(); }

// One event -> rigdio's API. Teams load only when opted in; anthems and the
// victory anthem have no reliable cue in memory, so the streamer plays those.
void PipeServer::toRigdio(const QJsonObject &e){
    const QString kind = e["event"].toString();
    if(rigdioDisabled || kind == "Clock Updated")   // ten a second
        return;
    QSettings settings;
    const QString url = settings.value("RigdioUrl").toString();
    if(url.isEmpty())
        return;
    const QString side = e["team"].toString().toLower();
    const int minute = (int)e["gameMinute"].toDouble();
    if(kind == "Teams Changed"){
        if(settings.value("RigdioLoadTeams", false).toBool())
            postRigdio(url, "/api/load", {{"home", stripSlashes(nameOf(e["home"]))},
                                          {"away", stripSlashes(nameOf(e["away"]))}});
    } else if(kind == "Goal"){
        postRigdio(url, "/api/goal", {{"side", side}, {"scorer", nameOf(e["scorer"])}});
    } else if(kind == "Own Goal"){
        // "team" is the player's side; the goal counts for the other one
        postRigdio(url, "/api/goal", {{"side", side == "home" ? "away" : "home"}});
        postRigdio(url, "/api/event", {{"event", "owngoal"}, {"player", nameOf(e["player"])}, {"minute", minute}});
    } else if(kind == "Card"){
        postRigdio(url, "/api/event", {{"event", e["card"].toString().toLower()}, {"player", nameOf(e["player"])}, {"minute", minute}});
    } else if(kind == "Player Sub"){
        postRigdio(url, "/api/event", {{"event", "sub"}, {"player", nameOf(e["playerIn"])}, {"minute", minute}});
    } else if(kind == "Clock Stopped"){
        const QString reason = e["reason"].toString();
        if(e["gameMinute"].toDouble() > 1 && reason != "Goal" && reason != "Own Goal" && reason != "Half End"
           && QRandomGenerator::global()->bounded(100) < settings.value("RigdioChantChance", 15).toInt())
            postRigdio(url, "/api/chant", QJsonObject());
    }
}

void PipeServer::postRigdio(const QString &url, const QString &path, const QJsonObject &body){
    QNetworkRequest req(QUrl(url + path));
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    req.setTransferTimeout(5000);
    QNetworkReply *reply = net->post(req, QJsonDocument(body).toJson(QJsonDocument::Compact));
    connect(reply, &QNetworkReply::finished, reply, [reply, path]{
        qDebug().noquote() << "rigdio" << path
                           << reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt()
                           << (reply->error() ? reply->errorString() : QString()) << reply->readAll();
        reply->deleteLater();
    });
}


void PipeServer::newConnection(){
    qDebug("Function Entered");
    while(server->hasPendingConnections()){
        PipeClient *client = new PipeClient(server->nextPendingConnection(),this);
        if(!lastTeamsChanged.isEmpty()){
            client->sendEvent(lastTeamsChanged);
            if(areStatsFound)
                client->sendEvent(lastStatsFound);
        }
        clients.push_back(client);
        if(!server->errorString().isEmpty())
            qDebug() << server->errorString();
    }
    if(!server->errorString().isEmpty())
        qDebug() << server->errorString();
    dbgReturn();
}
//TODO handle connections and incoming messages
void PipeServer::newEvent(match_event event){
    qDebug("Function Entered");
    broadcastEvent(event.toJSON(),event.when->match);
    dbgReturn();
}


void PipeServer::table_lost(match_time *when){
    qDebug("Function Entered");
    areStatsFound = false;
    QJsonObject event{
        {"type","Event"},
        {"event","Stats Lost"},
        {"timestamp",when->timestamp},
        {"gameMinute",when->gameMinute},
        {"injuryMinute",std::isnan(when->injuryMinute) ? QJsonValue(true) : QJsonValue(when->injuryMinute)}
    };
    if(when->injuryMinute < 0)
        event.remove("injuryMinute");
    broadcastEvent(QJsonDocument(event),when->match);
    dbgReturn();
}

void PipeServer::table_found(match_time *when){
    qDebug("Function Entered");
    areStatsFound = true;
    QJsonObject event{
        {"type","Event"},
        {"event","Stats Found"},
        {"timestamp",when->timestamp},
        {"gameMinute",when->gameMinute},
        {"injuryMinute",std::isnan(when->injuryMinute) ? QJsonValue(true) : QJsonValue(when->injuryMinute)},
        {"homeScore",when->match->homeScore},
        {"awayScore",when->match->awayScore}
    };
    if(when->injuryMinute < 0)
        event.remove("injuryMinute");
    lastStatsFound = QJsonDocument(event);
    broadcastEvent(lastStatsFound, when->match);
    dbgReturn();
}

void PipeServer::teamsChanged(Match *match){
    qDebug("Function Entered");
    QJsonArray homeArr, awayArr;
    for(int i = 0; i < match->home.nPlayers; ++i)
        homeArr.append(QJsonObject{ {"name",match->home.player[i].name}, {"playerId",(qint64)match->home.player[i].ID} });
    for(int i = 0; i < match->away.nPlayers; ++i)
        awayArr.append(QJsonObject{ {"name",match->away.player[i].name}, {"playerId",(qint64)match->away.player[i].ID} });

    QJsonObject event{
        {"type","Event"},
        {"event","Teams Changed"},
        {"timestamp",match->timestamp()},
        {"home",
            QJsonObject {
                {"name",match->home.name},
                {"id",(qint64)match->home.ID},
                {"players",homeArr}
            }
        },
        {"away",
            QJsonObject{
                {"name",match->away.name},
                {"id",(qint64)match->away.ID},
                {"players",awayArr}
            }
        }
    };
    lastTeamsChanged = QJsonDocument(event);
    broadcastEvent(lastTeamsChanged, match);
    dbgReturn();
}

void PipeServer::broadcastEvent(QJsonDocument event, Match *match, qint64 timestamp){
    qDebug("Function Entered");
    QFile log(match->applyFilenameFormat(QSettings().value("EventLogFile", "SEN_P-AI_Events.log").toString(),timestamp));
    if(log.open(QIODevice::ReadWrite | QIODevice::Text | QIODevice::Append)){
        log.write(event.toJson());
        log.close();
    }
    for(int i = 0; i < clients.size(); ++i){
        if(clients[i]->valid())
            clients[i]->sendEvent(event);
        else{
            qDebug("client invalid, removing");
            clients[i]->deleteLater();
            clients.erase(clients.begin() + i);
            --i;
        }
    }
    toRigdio(event.object());
    dbgReturn();
}
