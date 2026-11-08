FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 DB_PATH=/data/avtomaximus.db LEAD_PORT=8080
WORKDIR /app
COPY bot.py config.py texts.py ./
RUN mkdir -p /data
EXPOSE 8080
CMD ["python", "bot.py"]
