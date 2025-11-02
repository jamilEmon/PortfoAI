from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import cloudinary
import cloudinary.uploader
import requests
from django.views.decorators.http import require_http_methods
import json
from django.http import JsonResponse
from .models import Review
import logging
import io
          
import os
import google.generativeai as genai # Import Gemini library
from bs4 import BeautifulSoup # Import BeautifulSoup for web scraping

# Get an instance of a logger
logger = logging.getLogger(__name__)

cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# Configure Gemini API
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

# Initialize Gemini model
gemini_model = genai.GenerativeModel('gemini-2.0-flash-001')

# Create your views here.
def take_screenshot(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    browser.get(url)

    total_height = browser.execute_script("return document.body.parentNode.scrollHeight")

    browser.set_window_size(1200, total_height)

    screenshot = browser.get_screenshot_as_png()

    browser.quit()

    sanitized_url = url.replace('http://', '').replace('https://', '').replace('/', '_').replace(':', '_')

    upload_response = cloudinary.uploader.upload(
        io.BytesIO(screenshot),
        folder="screenshots",
        public_id=f"{sanitized_url}.png",
        resource_type='image'
    )
    
    return upload_response['url']

def scrape_website_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text from common sections
        content_parts = []
        
        # Headings
        for tag in ['h1', 'h2', 'h3']:
            for heading in soup.find_all(tag):
                content_parts.append(heading.get_text(separator=' ', strip=True))

        # Paragraphs
        for p in soup.find_all('p'):
            content_parts.append(p.get_text(separator=' ', strip=True))

        # Specific sections (e.g., 'about', 'projects', 'contact')
        for section_id in ['about', 'projects', 'contact', 'portfolio']:
            section = soup.find(id=section_id)
            if section:
                content_parts.append(section.get_text(separator=' ', strip=True))
        
        # Limit content to 2000-3000 characters
        full_content = " ".join(content_parts)
        if len(full_content) > 3000:
            full_content = full_content[:3000]
        elif len(full_content) < 2000:
            # Try to get more content if it's too short, e.g., from body
            body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
            full_content = (full_content + " " + body_text)[:3000]

        return full_content.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping website {url}: {e}", exc_info=True)
        return ""
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping {url}: {e}", exc_info=True)
        return ""

def get_review(url):
    try:
        scraped_text = scrape_website_content(url)
        if not scraped_text:
            return "Failed to scrape website content for review."

        prompt = (
            f"Please provide a concise, professional, and actionable portfolio review for the website at this URL: {url}. "
            f"Focus on design/layout, project showcase, navigation, readability, and overall impression. "
            f"Here is some scraped content from the website:\n\n{scraped_text}"
        )
        
        response = gemini_model.generate_content(prompt)
        review_text = response.text.strip()
        return review_text
    except Exception as e:
        logger.error(f"Error getting review from Gemini: {e}", exc_info=True)
        return "Failed to generate review."

@require_http_methods(["POST"])
def submit_url(request):
    try:
        data = json.loads(request.body)
        domain = data.get('domain')

        if not domain:
            logger.error("Domain not provided in the request.")
            return JsonResponse({"status": "error", "message": "Domain not provided"}, status=400)

        website_screenshot = None
        try:
            website_screenshot = take_screenshot(domain)
            if not website_screenshot:
                logger.error(f"Failed to take screenshot for domain: {domain}")
                return JsonResponse({"status": "error", "message": "Failed to take screenshot"}, status=500)
        except Exception as e:
            logger.error(f"Error taking screenshot for {domain}: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": f"Error taking screenshot: {e}"}, status=500)

        website_review = ""
        try:
            website_review = get_review(domain) # Pass domain for text scraping
            if not website_review:
                logger.warning(f"No review text received for domain: {domain}")
                # Continue even if no review, but log it
        except Exception as e:
            logger.error(f"Error getting review for domain {domain}: {e}", exc_info=True)
            # Continue with empty review if there's an error, but log it

        new_review_object = Review(
            site_url = domain,
            site_image_url = website_screenshot,
            feedback = website_review,
        )
        new_review_object.save(using='default')

        review_id = str(new_review_object.id)

        response_data = {
            'website_screenshot': website_screenshot,
            'website_review': website_review,
            'review_id': review_id,
        }

        return JsonResponse(response_data)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        logger.error(f"An unexpected error occurred in submit_url: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": f"An unexpected server error occurred: {e}"}, status=500)

@require_http_methods(["POST"])
def feedback(request):
    data = json.loads(request.body)
    review_id = data.get('id')
    feedback_type = data.get('type')

    try:
        review = Review.objects.get(pk=review_id)
        review.user_rating = feedback_type
        review.save()

        return JsonResponse({"status": "success", "message": "Feedback submitted"})
    except Review.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Review not found"})

def index(request):
    return render(request, 'index.html')
