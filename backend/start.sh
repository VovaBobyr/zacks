#!/bin/bash
set -e

# Start the cron daemon in the background
cron

# Run the Flask application
# Use Gunicorn for a production-ready server
exec gunicorn --bind 0.0.0.0:5001 "main:create_app()" 