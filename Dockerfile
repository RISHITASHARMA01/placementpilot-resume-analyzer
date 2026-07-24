FROM eclipse-temurin:21-jdk-jammy AS build

WORKDIR /app
COPY backend-java backend-java
RUN mkdir -p build/classes \
    && javac -d build/classes backend-java/src/main/java/com/placementpilot/ResumeAnalyzerServer.java

FROM eclipse-temurin:21-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/build/classes build/classes
COPY backend-python backend-python
COPY frontend frontend

ENV PYTHON_BIN=python3
EXPOSE 8080

CMD ["sh", "-c", "java -cp build/classes com.placementpilot.ResumeAnalyzerServer ${PORT:-8080}"]
