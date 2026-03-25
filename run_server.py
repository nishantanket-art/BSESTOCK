import traceback

try:
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="debug")
except Exception as e:
    with open("crash_debug.txt", "w") as f:
        f.write("CRASHED:\n" + traceback.format_exc())
