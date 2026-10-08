# Questions and deviations for the owner

## Source edits beyond the spec's three portability edits (spec 2.2)

The spec allows exactly three MinGW portability edits plus the `clock_updated` declaration. Building and running needed three more. None changes behaviour on a build where upstream already worked:

1. `src/Match.cpp`: `#include <cstring>` (MSVC pulled it in transitively for `std::strncpy`/`std::strncmp`).
2. `src/Match.cpp:558,577`: `f.get<uint32_t>()` becomes `f.template get<uint32_t>()`. `f` has a dependent type; MSVC accepts the missing `template` keyword, GCC cannot parse it and has no flag to allow it.
3. `src/main.cpp:24-28`: the debug message handler did `std::strchr(context.function,'(')-1` unconditionally. Messages emitted inside the release Qt DLLs carry no context (`function == NULL`), so any Qt-internal warning crashed the handler. Under Wine, Qt warns `EnableNonClientDpiScaling() failed` inside `WM_NCCREATE`; the crash there made `CreateWindowEx` fail and the main window never appeared. The handler now treats a missing function name as empty; such messages are logged as `...(line   0 of )`. Messages with a function name are formatted exactly as before.

Cosmetic, left as upstream: with GCC's `__PRETTY_FUNCTION__`, constructors have no return type before the name, so the debug log prints e.g. `tatTableReader::StatTableReader` (first character dropped). The format code is upstream's and unchanged.
