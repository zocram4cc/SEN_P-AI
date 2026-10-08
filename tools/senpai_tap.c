/* senpai_tap: record SEN:P-AI pipe frames exactly as received.
   Usage: senpai_tap.exe OUTFILE   (run in the game's WINEPREFIX) */
#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

static int read_all(HANDLE h, void *buf, DWORD n) {
    DWORD got = 0;
    while (got < n) {
        DWORD r = 0;
        if (!ReadFile(h, (char *)buf + got, n - got, &r, NULL) || r == 0) return 0;
        got += r;
    }
    return 1;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: senpai_tap OUTFILE\n"); return 2; }
    HANDLE h;
    for (;;) {
        h = CreateFileA("\\\\.\\pipe\\SEN_P-AI", GENERIC_READ | GENERIC_WRITE, 0, NULL,
                        OPEN_EXISTING, 0, NULL);
        if (h != INVALID_HANDLE_VALUE) break;
        Sleep(500);
    }
    FILE *out = fopen(argv[1], "ab");
    if (!out) return 1;
    for (;;) {
        uint8_t len[4];
        if (!read_all(h, len, 4)) break;
        uint32_t n = len[0] | len[1] << 8 | len[2] << 16 | (uint32_t)len[3] << 24;
        char *buf = malloc(n);
        if (!buf || !read_all(h, buf, n)) break;
        fwrite(len, 1, 4, out);
        fwrite(buf, 1, n, out);
        fflush(out);
        free(buf);
    }
    fclose(out);
    CloseHandle(h);
    return 0;
}
