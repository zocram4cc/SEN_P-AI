/* regions: read-only view of a process's memory, as SEN:P-AI sees it.
   regions.exe EXE list | dump BASEHEX SIZE OUT | scan U32 [REGIONSIZE] */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static DWORD find_pid(const char *exe) {
    PROCESSENTRY32 e; e.dwSize = sizeof e; DWORD pid = 0;
    HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (Process32First(s, &e))
        do { if (_stricmp(e.szExeFile, exe) == 0) { pid = e.th32ProcessID; break; } }
        while (Process32Next(s, &e));
    CloseHandle(s);
    return pid;
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: regions EXE list|dump|scan ...\n"); return 2; }
    DWORD pid = find_pid(argv[1]);
    if (!pid) { fprintf(stderr, "%s not running\n", argv[1]); return 1; }
    HANDLE h = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!h) { fprintf(stderr, "OpenProcess failed: %lu\n", GetLastError()); return 1; }
    MEMORY_BASIC_INFORMATION mi; uintptr_t a = 0;
    if (!strcmp(argv[2], "list")) {
        while (VirtualQueryEx(h, (void *)a, &mi, sizeof mi) > 0) {
            printf("%llx\t%llx\t%lx\t%lx\t%lx\n", (unsigned long long)(uintptr_t)mi.BaseAddress,
                   (unsigned long long)mi.RegionSize, mi.State, mi.Type, mi.Protect);
            a = (uintptr_t)mi.BaseAddress + mi.RegionSize;
        }
        return 0;
    }
    if (!strcmp(argv[2], "dump") && argc == 6) {
        uintptr_t base = (uintptr_t)strtoull(argv[3], NULL, 16);
        size_t size = (size_t)strtoull(argv[4], NULL, 0);
        char *buf = malloc(size); SIZE_T got = 0;
        if (!buf || !ReadProcessMemory(h, (void *)base, buf, size, &got)) { fprintf(stderr, "read failed\n"); return 1; }
        FILE *f = fopen(argv[5], "wb"); fwrite(buf, 1, got, f); fclose(f);
        printf("%zu bytes\n", (size_t)got);
        return 0;
    }
    if (!strcmp(argv[2], "scan") && argc >= 4) {
        uint32_t want = (uint32_t)strtoul(argv[3], NULL, 0);
        size_t only = argc > 4 ? (size_t)strtoull(argv[4], NULL, 0) : 0;
        while (VirtualQueryEx(h, (void *)a, &mi, sizeof mi) > 0) {
            uintptr_t base = (uintptr_t)mi.BaseAddress; size_t sz = mi.RegionSize;
            if ((mi.State & MEM_COMMIT) && (mi.Type & MEM_PRIVATE) && (mi.Protect & PAGE_READWRITE)
                && (!only || sz == only)) {
                uint32_t *buf = malloc(sz); SIZE_T got = 0;
                if (buf && ReadProcessMemory(h, (void *)base, buf, sz, &got))
                    for (size_t i = 0; i < got / 4; i++)
                        if (buf[i] == want)
                            printf("%llx\t%llx\t%llx\n", (unsigned long long)(base + i * 4),
                                   (unsigned long long)base, (unsigned long long)sz);
                free(buf);
            }
            a = base + sz;
        }
        return 0;
    }
    fprintf(stderr, "bad arguments\n");
    return 2;
}
