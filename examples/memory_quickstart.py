from genaiscope.memory import MemoryStore

memory = MemoryStore()
memory.add("User prefers short CTO-level answers.", memory_type="preference")
print(memory.search("answer style"))
