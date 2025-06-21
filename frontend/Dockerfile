# Stage 1: Build the React application
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . ./

# Add execute permissions to fix build issues in some environments
RUN chmod -R +x node_modules

RUN npm run build

# Stage 2: Serve the application from Nginx
FROM nginx:1.21-alpine

# Copy the build output to replace the default Nginx content.
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 