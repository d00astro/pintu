# TODO: migrate to FastAPI
from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse, FileResponse, HTMLResponse
from config import  get_settings
from uvicorn import run
import datetime
import time
import subprocess
import peripherals_io


config = get_settings()
log = config.log

def create_api() -> FastAPI:
	fast_api = FastAPI(
		title="Pintu API",
		description="""By [Anders Astrom](https://github.com/d00astro)

A basic API for "smart door" control
""",
		version=config.version,
		openapi_tags=[
			{"name": "status", "description": "Status functions"},
		],
#		root_path=config.route_prefix
	)
	return fast_api


api = create_api()


@api.post("/reboot")
def reboot():
	subprocess.call(["reboot", "now"])


@api.get("/view")
def gate(*, request: Request):
	timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	open_url = f"{request.url}/open"
	refresh_url = request.url
	image_url = f"{request.url}/image_{timestamp}.jpg"
	return HTMLResponse(f"""
<html>
	<body bgcolor="#000000" text="#FFFFFF">
		<h1>[ <a href='{open_url}'>Open</a> ]</h1><br/>
		<a href='{refresh_url}'>
			<img src='{image_url}' alt='Open Gate'>
		</a>
	</body>
</html>
""")


@api.get("/view/open")
def open_view():
	peripherals_io.open_door()
	return RedirectResponse(url="/view")


@api.get("/view/image_{timestamp}.jpg")
def image(timestamp: str):
	log.info(f"Requesting image:{timestamp}")
	return FileResponse("static/fruits.png", media_type='image/png')


@api.post("/open")
def open_gate():
	peripherals_io.open_door()


@api.on_event("startup")
async def startup_event():
	config.log.info("Starting up...")
	peripherals_io.initialize()


@api.on_event("shutdown")
async def shutdown_event():
	config.log.info("Shutting down...")
	peripherals_io.graceful_shutdown()


# For simplified debug purposes only
if __name__ == "__main__":
	run(api, host="0.0.0.0", port=config.listen_port)
