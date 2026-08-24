"""V17 entry point: load the existing monitor, apply hotfixes, then run it."""
import monitor
import runtime_hotfix
runtime_hotfix.apply(monitor)
monitor.main()
