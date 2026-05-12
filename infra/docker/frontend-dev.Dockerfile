FROM node:22-slim

ENV NODE_ENV=development

WORKDIR /workspace/ReactProje

COPY ReactProje/package*.json ./
RUN npm ci

COPY ReactProje ./

EXPOSE 5173
