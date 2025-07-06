from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io
from weasyprint import HTML

from openai import OpenAI
client = OpenAI()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def input_form(request: Request):
    return templates.TemplateResponse("input_form.html", {"request": request})

@app.post("/review", response_class=HTMLResponse)
async def review(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    summary: str = Form(...),
    experience: str = Form(...),
    education: str = Form(...),
):
    prompt = f"Rewrite this experience and education into professional resume bullet points:\nExperience:\n{experience}\nEducation:\n{education}"
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ]
    )
    rewritten_text = completion.choices[0].message.content.strip()

    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "summary": summary,
            "rewritten": rewritten_text,
        },
    )

@app.post("/generate-pdf")
async def generate_pdf(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    summary: str = Form(...),
    rewritten: str = Form(...),
):
    html_content = templates.get_template("resume_template.html").render(
        full_name=full_name,
        email=email,
        phone=phone,
        summary=summary,
        rewritten=rewritten,
    )
    pdf = HTML(string=html_content).write_pdf()
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"},
    )