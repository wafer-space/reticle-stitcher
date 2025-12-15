import os
import pya

print(f"Reading layout: {input}")

ly = pya.Layout()
ly.read(input)

drc_interpreter = pya.Interpreter.ruby_interpreter()
drc_interpreter.define_variable('layout', ly)

macro = os.path.join(os.path.dirname(__file__), "fill.drc")

print(f"Executing macro: {macro}")
pya.Macro(macro).run()

print(f"Writing layout: {output}")
ly.write(output)
