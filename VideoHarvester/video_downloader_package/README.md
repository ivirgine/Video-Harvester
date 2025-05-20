# Video Downloader App

A versatile web-based video downloader application that supports multiple platforms and download options.

## Features

- Multi-platform video downloading (YouTube, Vimeo, Dailymotion)
- Audio-only download capability
- Scheduled download system
- Download history tracking
- Responsive web interface

## Deployment Instructions for Render.com

1. Create a new Render.com account at [render.com](https://render.com)
2. Create a new Web Service
   - Connect to GitHub (upload this package to a GitHub repository)
   - Select Python runtime
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn main:app`
   - Select Free plan

3. Add a PostgreSQL database
   - Create a new PostgreSQL database in Render
   - Copy the Internal Database URL to your Web Service's environment variables

4. Set required environment variables:
   - `DATABASE_URL` - Your PostgreSQL database URL
   - `SESSION_SECRET` - A random string for session security (e.g., `openssl rand -hex 32`)

5. Deploy your application

## Using with AppCreator24

1. Get your Render.com app URL after deployment (e.g., `https://video-downloader.onrender.com`)
2. Create a new app in AppCreator24
3. Use the WebView App template
4. Set your app URL to the Render.com URL
5. Configure file download permissions
6. Add monetization as desired
7. Build and publish your app

## Maintenance

- The app uses a PostgreSQL database to store download history and scheduled tasks
- Temporary downloaded files are automatically cleaned up after serving