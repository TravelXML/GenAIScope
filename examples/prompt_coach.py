from genaiscope.memory import MemoryStore

memory = MemoryStore()
item = memory.add_prompt("Summarize this properly.")
print(item.prompt_score)
print(item.prompt_comments)
