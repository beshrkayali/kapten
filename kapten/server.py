from starlette.applications import Starlette
from starlette.responses import JSONResponse

from . import __version__
from .log import logger
from .tool import Kapten

app = Starlette(debug=True)
app.state.client = None


@app.route("/version")
async def version(request):
    return JSONResponse({"kapten": __version__})


@app.route("/webhook/dockerhub", methods=["POST"])
async def dockerhub_webhook(request):
    payload = await request.json()

    # TODO: Validate any service image is part of the callback url by:
    #
    #       Fetching repositories and set in app.state on server start
    #         - or -
    #       Don't require --service argument to allow all running services/images
    #
    #       Validate: https://registry.hub.docker.com/u/5monkeys/testhook/

    callback_url = payload["callback_url"]
    if not callback_url.startswith("https://registry.hub.docker.com/u/"):
        # TODO: Return bad request
        raise ValueError()

    # TODO: Ack callback url

    repository = payload["repository"]["repo_name"]
    tag = payload["push_data"]["tag"]
    image_name = "{}:{}".format(repository, tag)

    client = app.state.client
    services = client.list_services(image_name)
    latest_digest = client.get_latest_digest(image_name)

    updated_services = []
    for service in services:
        client.update_service(service)
        updated_services.append(service.name)

    # result = app.state.client.update_services(services)

    return JSONResponse(
        {"services": updated_services, "image": image_name, "digest": latest_digest}
    )


def run(client: Kapten, host: str, port: int):
    import uvicorn

    logger.info("Starting Kapten {} server ...".format(__version__))
    app.state.client = client
    uvicorn.run(app, host=host, port=port)
