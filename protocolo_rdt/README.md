# Copilot Instructions for RDT Network Emulator

## Project Overview
This codebase implements a network emulator for the Alternating Bit and Go-Back-N protocols, based on J.F. Kurose's simulator. It is designed for educational purposes, simulating unidirectional or bidirectional data transfer between two entities (A and B) with support for packet loss and corruption.

## Key Files
- `rdt.c`: Contains all code, including protocol logic (to be implemented by students) and the network emulation layer (do not modify).

## Architecture & Data Flow
- **Layer 5 to Layer 4:** `A_output()` and `B_output()` are called when a message arrives from the application layer.
- **Layer 4 to Layer 3:** Use `tolayer3()` to send packets to the network layer.
- **Layer 3 to Layer 4:** `A_input()` and `B_input()` are called when a packet arrives from the network.
- **Layer 4 to Layer 5:** Use `tolayer5()` to deliver data to the application layer.
- **Timers:** Use `starttimer()` and `stoptimer()` for retransmission logic.

## Developer Workflow
- **Build:** Compile with `gcc rdt.c -o rdt` (no external dependencies).
- **Run:** Execute with `./rdt` and follow interactive prompts for simulation parameters.
- **Debugging:** Set `TRACE` level (prompted at runtime) for verbose output.
- **Testing:** The simulation is self-contained; test by running and observing output.

## Project-Specific Conventions
- **Protocol Implementation:** Only modify the seven student routines (`A_output`, `A_input`, `A_timerinterrupt`, `A_init`, `B_output`, `B_input`, `B_timerinterrupt`, `B_init`).
- **Packet Structure:** Always use the provided `struct pkt` and `struct msg` for communication.
- **No External Libraries:** All logic must be implemented in C using the provided framework.
- **Bidirectional Mode:** Set `#define BIDIRECTIONAL 1` and implement `B_output()` for extra credit.
- **Do Not Modify Emulator Code:** The network emulation section (below the student routines) must remain unchanged.

## Examples
- To send a packet from A: call `tolayer3(A, packet);`
- To start a timer for A: call `starttimer(A, timeout);`
- To deliver data to the application: call `tolayer5(A, data);`

## References
- For more details, see comments in `rdt.c` and the provided assignment PDF/docx.

---
If any section is unclear or missing details, please provide feedback to improve these instructions.