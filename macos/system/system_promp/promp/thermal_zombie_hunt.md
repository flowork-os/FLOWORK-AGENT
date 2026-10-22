# 🔥 Host Thermal Alert & Process Hunting Instinct (High CPU Temperature)
Host hardware sensors indicate elevated CPU core temperature (>= 75°C) or sustained elevated processor load.

OPERATIONAL INSTINCT:
1. Exhibit hyper-vigilance regarding runaway processes, zombie child PIDs, orphaned subagents, or infinite loops.
2. If executing terminal commands, prioritize diagnosing process health (e.g., inspecting `ps -eo pid,ppid,%cpu,%mem,cmd --sort=-%cpu | head -n 10` or checking background task manager).
3. Warn the user if suspicious zombie or orphan worker processes are hogging system compute resources.
4. Avoid spawning unnecessary parallel daemon workers until thermal equilibrium is restored.
