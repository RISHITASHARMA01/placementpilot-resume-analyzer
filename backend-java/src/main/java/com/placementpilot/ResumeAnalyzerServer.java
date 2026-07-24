package com.placementpilot;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class ResumeAnalyzerServer {
    private static final int DEFAULT_PORT = 8080;
    private static final int MAX_REQUEST_BYTES = 2_000_000;

    public static void main(String[] args) throws IOException {
        int port = resolvePort(args);
        Path projectRoot = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        Path frontendDir = projectRoot.resolve("frontend").normalize();
        Path analyzerScript = projectRoot.resolve("backend-python").resolve("analyzer.py").normalize();

        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/api/health", new HealthHandler(analyzerScript));
        server.createContext("/api/analyze", new AnalyzeHandler(projectRoot, analyzerScript));
        server.createContext("/", new StaticFileHandler(frontendDir));
        server.setExecutor(Executors.newFixedThreadPool(Math.max(4, Runtime.getRuntime().availableProcessors())));
        server.start();

        System.out.println("PlacementPilot Resume Analyzer running at http://localhost:" + port);
        System.out.println("Project root: " + projectRoot);
    }

    private static int resolvePort(String[] args) {
        if (args.length > 0) {
            return Integer.parseInt(args[0]);
        }
        String envPort = System.getenv("PORT");
        if (envPort != null && !envPort.isBlank()) {
            return Integer.parseInt(envPort);
        }
        return DEFAULT_PORT;
    }

    private static void addCors(HttpExchange exchange) {
        Headers headers = exchange.getResponseHeaders();
        headers.set("Access-Control-Allow-Origin", "*");
        headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        headers.set("Access-Control-Allow-Headers", "Content-Type");
    }

    private static void sendJson(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        addCors(exchange);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }

    private static void sendEmpty(HttpExchange exchange, int status) throws IOException {
        addCors(exchange);
        exchange.sendResponseHeaders(status, -1);
        exchange.close();
    }

    private static byte[] readLimited(InputStream input, int maxBytes) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] chunk = new byte[8192];
        int total = 0;
        int read;
        while ((read = input.read(chunk)) != -1) {
            total += read;
            if (total > maxBytes) {
                throw new IOException("Request body is too large.");
            }
            buffer.write(chunk, 0, read);
        }
        return buffer.toByteArray();
    }

    private static String jsonEscape(String value) {
        StringBuilder escaped = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char character = value.charAt(i);
            switch (character) {
                case '"' -> escaped.append("\\\"");
                case '\\' -> escaped.append("\\\\");
                case '\b' -> escaped.append("\\b");
                case '\f' -> escaped.append("\\f");
                case '\n' -> escaped.append("\\n");
                case '\r' -> escaped.append("\\r");
                case '\t' -> escaped.append("\\t");
                default -> {
                    if (character < 0x20) {
                        escaped.append(String.format("\\u%04x", (int) character));
                    } else {
                        escaped.append(character);
                    }
                }
            }
        }
        return escaped.toString();
    }

    private static final class HealthHandler implements HttpHandler {
        private final Path analyzerScript;

        private HealthHandler(Path analyzerScript) {
            this.analyzerScript = analyzerScript;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCors(exchange);
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendEmpty(exchange, 204);
                return;
            }
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendJson(exchange, 405, "{\"ok\":false,\"error\":\"Method not allowed\"}");
                return;
            }
            String body = "{\"ok\":true,\"service\":\"java-api\",\"pythonAnalyzer\":" + Files.exists(analyzerScript) + "}";
            sendJson(exchange, 200, body);
        }
    }

    private static final class AnalyzeHandler implements HttpHandler {
        private final Path projectRoot;
        private final Path analyzerScript;

        private AnalyzeHandler(Path projectRoot, Path analyzerScript) {
            this.projectRoot = projectRoot;
            this.analyzerScript = analyzerScript;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCors(exchange);
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendEmpty(exchange, 204);
                return;
            }
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendJson(exchange, 405, "{\"ok\":false,\"error\":\"Method not allowed\"}");
                return;
            }
            if (!Files.exists(analyzerScript)) {
                sendJson(exchange, 500, "{\"ok\":false,\"error\":\"Python analyzer was not found\"}");
                return;
            }

            byte[] requestBody;
            try {
                requestBody = readLimited(exchange.getRequestBody(), MAX_REQUEST_BYTES);
            } catch (IOException exception) {
                sendJson(exchange, 413, "{\"ok\":false,\"error\":\"" + jsonEscape(exception.getMessage()) + "\"}");
                return;
            }

            if (requestBody.length == 0) {
                sendJson(exchange, 400, "{\"ok\":false,\"error\":\"Request body is required\"}");
                return;
            }

            ProcessBuilder processBuilder = new ProcessBuilder(resolvePythonCommand(), analyzerScript.toString());
            processBuilder.directory(projectRoot.toFile());

            try {
                Process process = processBuilder.start();
                try (OutputStream processInput = process.getOutputStream()) {
                    processInput.write(requestBody);
                }

                boolean completed = process.waitFor(20, TimeUnit.SECONDS);
                String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
                String error = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);

                if (!completed) {
                    process.destroyForcibly();
                    sendJson(exchange, 504, "{\"ok\":false,\"error\":\"Analysis timed out\"}");
                    return;
                }
                if (process.exitValue() != 0) {
                    sendJson(exchange, 502, "{\"ok\":false,\"error\":\"Analyzer failed\",\"details\":\"" + jsonEscape(error) + "\"}");
                    return;
                }
                sendJson(exchange, 200, output.isBlank() ? "{\"ok\":false,\"error\":\"Analyzer returned empty output\"}" : output);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                sendJson(exchange, 500, "{\"ok\":false,\"error\":\"Analysis was interrupted\"}");
            } catch (IOException exception) {
                sendJson(exchange, 500, "{\"ok\":false,\"error\":\"" + jsonEscape(exception.getMessage()) + "\"}");
            }
        }

        private String resolvePythonCommand() {
            String configured = System.getenv("PYTHON_BIN");
            if (configured != null && !configured.isBlank()) {
                return configured;
            }
            return "python3";
        }
    }

    private static final class StaticFileHandler implements HttpHandler {
        private static final Map<String, String> MIME_TYPES = Map.ofEntries(
                Map.entry(".html", "text/html; charset=utf-8"),
                Map.entry(".css", "text/css; charset=utf-8"),
                Map.entry(".js", "application/javascript; charset=utf-8"),
                Map.entry(".json", "application/json; charset=utf-8"),
                Map.entry(".png", "image/png"),
                Map.entry(".jpg", "image/jpeg"),
                Map.entry(".jpeg", "image/jpeg"),
                Map.entry(".svg", "image/svg+xml")
        );

        private final Path frontendDir;

        private StaticFileHandler(Path frontendDir) {
            this.frontendDir = frontendDir;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCors(exchange);
            String method = exchange.getRequestMethod();
            if (!"GET".equalsIgnoreCase(method) && !"HEAD".equalsIgnoreCase(method)) {
                sendJson(exchange, 405, "{\"ok\":false,\"error\":\"Method not allowed\"}");
                return;
            }

            String requestPath = URLDecoder.decode(exchange.getRequestURI().getPath(), StandardCharsets.UTF_8);
            if (requestPath.equals("/")) {
                requestPath = "/index.html";
            }

            Path file = frontendDir.resolve(requestPath.substring(1)).normalize();
            if (!file.startsWith(frontendDir)) {
                sendJson(exchange, 403, "{\"ok\":false,\"error\":\"Forbidden\"}");
                return;
            }
            if (Files.isDirectory(file)) {
                file = file.resolve("index.html").normalize();
            }
            if (!Files.exists(file)) {
                byte[] body = "Not found".getBytes(StandardCharsets.UTF_8);
                exchange.sendResponseHeaders(404, body.length);
                try (OutputStream output = exchange.getResponseBody()) {
                    output.write(body);
                }
                return;
            }

            byte[] body = Files.readAllBytes(file);
            exchange.getResponseHeaders().set("Content-Type", contentType(file));
            exchange.sendResponseHeaders(200, "HEAD".equalsIgnoreCase(method) ? -1 : body.length);
            if (!"HEAD".equalsIgnoreCase(method)) {
                try (OutputStream output = exchange.getResponseBody()) {
                    output.write(body);
                }
            } else {
                exchange.close();
            }
        }

        private String contentType(Path file) {
            String name = file.getFileName().toString().toLowerCase(Locale.ROOT);
            for (Map.Entry<String, String> entry : MIME_TYPES.entrySet()) {
                if (name.endsWith(entry.getKey())) {
                    return entry.getValue();
                }
            }
            return "application/octet-stream";
        }
    }
}
