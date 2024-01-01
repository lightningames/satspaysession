import http

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# from loguru import logger

from .exchange_rates import fiat_amount_as_satoshis
from .utils import get_lnbits_satspay, is_https_url

TITLE = "satspay session"
APP_DESC = "simple url bridge to lnbits satspay extension"

app = FastAPI(
    title=TITLE,
    description=APP_DESC,
    version="0.0.1 alpha",
    contact={
        "name": "bitkarrot",
        "url": "http://github.com/bitkarrot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://mit-license.org/",
    },
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")


async def handle_params(*args):
    """
    Handle the parameters passed to the function.

    Args:
        *args: Variable length argument list.

    Returns:
        str: The response URL if the parameters are valid and the
                function is able to generate a response URL.
            If the number of arguments is 2, the response URL is generated
                using the `amount` and `description` arguments.
            If the number of arguments is 3, the response URL is generated
                using the `sats`, `description`, and `fiat` arguments.
            If the number of arguments is neither 2 nor 3, an error message is returned.

    Raises:
        None
    """
    if len(args) == 2:
        amount, description = args
        res_url = await get_lnbits_satspay(int(amount), description)
        print("2 args, handle params response: ", res_url)
        return res_url
    elif len(args) == 3:
        fiat, amount, description = args
        if isinstance(amount, int):
            print("fiat: ", fiat.upper(), "amt: ", int(amount),"description: ", description)
            sats =  await fiat_amount_as_satoshis(int(amount), fiat.upper())
            print("fiat amt in satoshis: ", sats)
            res_url = await get_lnbits_satspay(sats, description)
            print("3 args, handle params response: ", res_url)
            return res_url
    else:
        return f"Endpoint for {fiat}, No amount provided as integer."


@app.get("/fiat/{fiat}/amt/{amount}")
async def dynamic_endpoint(fiat: str, amount: int):
    """
    An asynchronous function that handles a dynamic endpoint.

    Parameters:
    - fiat (str): The fiat currency.
    - amount (int): The amount.

    Returns:
    - The URL to redirect to if it is an HTTPS URL.
    - Otherwise, the URL itself.
    """
    res_url = await handle_params(fiat, amount, "")
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/fiat/{fiat}/amt/{amount}/desc/{description}")
async def dynamic_longendpoint(fiat: str, amount: int, description: str):
    """
    A function that handles a dynamic long endpoint.

    Parameters:
        fiat (str): The fiat currency.
        amount (int): The amount.
        description (str): The description.

    Returns:
        Union[RedirectResponse, str]: The result URL or a RedirectResponse if the URL is HTTPS.
    """
    res_url = await handle_params(fiat, amount, description)
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/amt/{amount}/desc/{description}")
async def dynamic_satendpoint(amount: int, description: str):
    """
    Endpoint for satoshis amount and description
    """
    res_url = await handle_params(amount, description)
    if is_https_url(res_url):
        return RedirectResponse(url=res_url, status_code=302)
    else:
        return res_url


@app.get("/")
async def initial_page(request: Request):
    """
    This function is the handler for the initial page of the application.

    Parameters:
        - request (Request): The request object containing information about the HTTP request.

    Returns:
        - TemplateResponse: The response containing the rendered "index.html" template.
    """
    fiat = "USD"
    description = "Meeting"
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "title": "SatsPay Link",
            "fiat": fiat,
            "description": description,
            "amount": 100,
        },
    )


@app.get("/thanks")
async def thanks_page(request: Request):
    """
    Get the thanks page.

    Args:
        request (Request): The incoming request object.

    Returns:
        TemplateResponse: The rendered thanks.html template.
    """
    return templates.TemplateResponse("thanks.html", context={"request": request})


@app.post("/thanks", status_code=http.HTTPStatus.ACCEPTED)
async def thanks_post(request: Request):
    """
    A handler for the HTTP POST request to '/thanks'.

    Parameters:
        request (Request): The incoming HTTP request object.

    Returns:
        TemplateResponse: The HTML template response for 'thanks.html'.
    """
    # Process the captured data as needed
    payload = await request.body()
    print("thanks data:", str(payload))
    return templates.TemplateResponse("thanks.html", context={"request": request})


@app.get("/about")
def about():
    """
    Get information about the application.
    """
    return "About"
