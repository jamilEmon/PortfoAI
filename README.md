This project, named __PortfoAI__, is a Django-based web application designed to provide automated, AI-powered reviews of portfolio websites.

__Core Functionality:__

1. __URL Submission:__ Users submit a portfolio URL through a simple web interface.

2. __Automated Analysis:__ The backend processes the URL by:

   - Taking a full-page screenshot of the website using __Selenium__.
   - Uploading the screenshot to __Cloudinary__ for hosting.
   - Scraping key text content from the website's HTML using __BeautifulSoup__.

3. __AI-Powered Review Generation:__ The scraped text is sent to __Google's Gemini AI model__ with a prompt to generate a professional review focusing on design, project showcases, and navigation.

4. __Display and Feedback:__ The application displays the screenshot and the AI-generated review to the user. The user can then provide feedback on the quality of the review ("great" or "poor").

__Technical Stack:__

- __Backend:__ Django

- __Frontend:__ HTML, Tailwind CSS, and vanilla JavaScript

- __Database:__ Configured with SQLite by default, with the model stored in the `review` app.

- __Key Libraries:__

  - `django`: Web framework
  - `google-generativeai`: For interacting with the Gemini AI model.
  - `selenium` & `beautifulsoup4`: For web automation and scraping.
  - `cloudinary`: For cloud-based image management.
  - `python-dotenv`: For managing environment variables.

In summary, PortfoAI is a well-structured application that automates the portfolio review process by combining web scraping with a powerful generative AI model to deliver instant feedback to users.
