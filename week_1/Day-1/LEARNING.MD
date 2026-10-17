# Day 1: First tool call

## Raw response, labelled
- `choices[0].message.role`: Who send/generated this response (`user` or `assistant` or `tool`)
- `choices[0].message.tool_calls[0].id`: Unique identifier of first function
- `choices[0].message.tool_calls[0].function.name`: Name of first function
- `choices[0].message.tool_calls[0].function.arguments`: Arguments of first function (why is it a string?)
- `choices[0].finish_reason`: Reason of ending (`tool_calls` because LLM needs tool call and `stop` because LLM got answer of user query)
- `usage.prompt_tokens` / `usage.completion_tokens`: Input tokens and output tokens

## Message order in a tool call
```text
YOU                          MODEL
 │                             │
 │  messages = [user question] │
 │ ─────── Call 1 ───────────► │
 │                             │ "I don't know the weather.
 │ ◄──────────────────────────  I need get_weather(city=Surat)"
 │                             │
 │ run get_weather() yourself  │
 │                             │
 │  messages = [user question, │
 │   assistant tool request,   │
 │   tool result]              │
 │ ─────── Call 2 ───────────► │
 │                             │
 │ ◄──────────────────────────  "It's 31°C and sunny in Surat."
```

## What worked / what broke / what surprised me
- ...