from genaiscope.tracing import LocalTracer

tracer = LocalTracer()
tracer.log(name="demo-call", input_text="hello", output_text="hi", model="local")
print(tracer.stats())
