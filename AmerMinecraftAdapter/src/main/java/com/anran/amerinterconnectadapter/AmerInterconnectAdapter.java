package com.anran.amerinterconnectadapter;

import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.*;
import org.bukkit.event.server.ServerLoadEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class AmerInterconnectAdapter extends JavaPlugin implements CommandExecutor, Listener {

    private FileConfiguration config;
    private ScheduledExecutorService scheduler;
    private int retryCount = 0;
    private BukkitRunnable heartbeatTask;

    @Override
    public void onEnable() {
        // 初始化配置文件
        saveDefaultConfig();
        config = getConfig();

        // 检查是否已经生成了Token
        if (!config.contains("token")) {
            String token = TokenGenerator.generateToken();
            config.set("token", token);
            saveConfig();
        }

        // 检查是否已经生成了amer_key
        if (!config.contains("amer_key")) {
            String amerKey = TokenGenerator.generateToken().substring(0, 6);
            config.set("amer_key", amerKey);
            saveConfig();
        }

        // 注册服务器
        if (!registerServer()) {
            getLogger().severe("服务器注册失败，插件将停止运行。");
            getServer().getPluginManager().disablePlugin(this);
            return;
        }

        // 注册命令
        this.getCommand("getamertoken").setExecutor(this);
        this.getCommand("getamerkey").setExecutor(this);
        this.getCommand("setamerkey").setExecutor(this);
        getLogger().info("Amer来咯,接住本喵~");

        // 注册事件监听器
        getServer().getPluginManager().registerEvents(this, this);

        // 启动心跳
        startHeartbeat();
    }

    @Override
    public void onDisable() {
        getLogger().info("Amer退下了，拜拜~");

        // 发送关闭消息
        closeServer();

        // 确保所有任务都已完成
        if (scheduler != null) {
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(10, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (command.getName().equalsIgnoreCase("getamertoken")) {
            // 检查发送者是否是OP
            if (sender.isOp()) {
                // 获取Token
                String token = config.getString("token");
                sender.sendMessage("你的Token来咯~ : " + token);
                return true;
            } else {
                // 发送者不是OP，告知没有权限
                sender.sendMessage("本Amer不告诉你,略略略~。");
                return true;
            }
        } else if (command.getName().equalsIgnoreCase("getamerkey")) {
            // 检查发送者是否是OP
            if (sender.isOp()) {
                // 获取密钥
                String amerKey = config.getString("amer_key");
                sender.sendMessage("当前密钥: " + amerKey);
                return true;
            } else {
                // 发送者不是OP，告知没有权限
                sender.sendMessage("你没有权限查看密钥哦~");
                return true;
            }
        } else if (command.getName().equalsIgnoreCase("setamerkey")) {
            // 检查发送者是否是OP
            if (sender.isOp()) {
                if (args.length == 1) {
                    config.set("amer_key", args[0]);
                    saveConfig();
                    sender.sendMessage("密钥已更新为: " + args[0]);
                    return true;
                } else {
                    sender.sendMessage("用法: /setamerkey <新密钥>");
                    return true;
                }
            } else {
                sender.sendMessage("你没有权限修改密钥哦~");
                return true;
            }
        }
        return false;
    }

    private boolean registerServer() {
        String token = config.getString("token");
        String message = String.format("{\"token\": \"%s\", \"action\": \"register\"}", token);
        String url = config.getString("api_url", "https://api.anran.xyz/mc/handle");
        try {
            int responseCode = sendHttpPostRequest(url, message);
            if (responseCode == 488) {
                getLogger().warning("无效的 token 或未注册的服务器，尝试重新注册...");
                if (retryCount < 3) { // 最多重试3次
                    retryCount++;
                    return registerServer();
                } else {
                    getLogger().severe("重试次数超过限制，注册失败。");
                    return false;
                }
            }
            return responseCode == HttpURLConnection.HTTP_OK;
        } catch (Exception e) {
            getLogger().severe("服务器注册失败: " + e.getMessage());
            return false;
        }
    }

    private void closeServer() {
        String token = config.getString("token");
        String message = String.format("{\"token\": \"%s\", \"action\": \"close\"}", token);
        String url = config.getString("api_url", "https://api.anran.xyz/mc/handle");
        try {
            sendHttpPostRequest(url, message);
        } catch (Exception e) {
            getLogger().severe("服务器关闭失败: " + e.getMessage());
        }
    }

    private int sendHttpPostRequest(String url, String body) {
        try {
            URL obj = new URL(url);
            HttpURLConnection con = (HttpURLConnection) obj.openConnection();
            con.setRequestMethod("POST");
            con.setRequestProperty("Content-Type", "application/json; utf-8");
            con.setRequestProperty("Accept", "application/json");
            con.setDoOutput(true);

            String jsonInputString = body;
            try (OutputStream os = con.getOutputStream()) {
                byte[] input = jsonInputString.getBytes("utf-8");
                os.write(input, 0, input.length);
            }

            int responseCode = con.getResponseCode();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                try (BufferedReader in = new BufferedReader(new InputStreamReader(con.getInputStream()))) {
                    String inputLine;
                    StringBuilder content = new StringBuilder();
                    while ((inputLine = in.readLine()) != null) {
                        content.append(inputLine);
                    }

                    // 解析 JSON 响应
                    JSONObject jsonResponse = (JSONObject) new org.json.simple.parser.JSONParser().parse(content.toString());
                    JSONArray messages = (JSONArray) jsonResponse.get("messages");
                    if (messages != null && !messages.isEmpty()) {
                        for (Object messageObj : messages) {
                            String message = (String) messageObj;
                            handleMessage(message);
                        }
                    }
                }
            } else {
                if (responseCode == 488) {
                    registerServer();
                }
                getLogger().severe("HTTP Error: " + responseCode);
            }
            return responseCode;
        } catch (Exception e) {
            getLogger().severe("HTTP Request Error: " + e.getMessage());
            return -1;
        }
    }

    private void sendEvent(String type, String senderName, String value) {
        String token = config.getString("token");
        JSONObject json = new JSONObject();
        json.put("token", token);
        json.put("type", type);
        json.put("senderName", senderName);
        json.put("value", value);

        String url = config.getString("api_url", "https://api.anran.xyz/mc/handle");
        sendHttpPostRequest(url, json.toString());
    }

    private void startHeartbeat() {
        if (heartbeatTask != null) {
            heartbeatTask.cancel();
        }
        long heartbeatInterval = config.getLong("heartbeat_interval", 10); // 默认10秒
        heartbeatTask = new BukkitRunnable() {
            @Override
            public void run() {
                sendEvent("心跳", "服务器", "");
            }
        };
        heartbeatTask.runTaskTimerAsynchronously(this, 200L, heartbeatInterval * 20L); // 每10秒执行一次
    }

    private void handleMessage(String message) {
        // 基本格式验证
        if (message == null || message.trim().isEmpty()) {
            getLogger().warning("收到的消息为空: " + message);
            return;
        }

        // 解析消息
        String[] parts = message.replaceAll("[\\[\\]]", "").split(", ");
        if (parts.length < 3) {
            getLogger().warning("收到的消息格式不正确: " + message);
            return;
        }
        String token = parts[0];
        String messageType = parts[1];
        String senderName = parts[2];
        String value = parts.length > 3 ? parts[3] : "";
        if (senderName.equals("服务器")) {
            String localToken = config.getString("token");
            if (token.equals(localToken)) {
                if ("消息".equals(messageType)) {
                    getServer().broadcastMessage(value);
                } else if ("指令".equals(messageType) || "指令v2".equals(messageType)) {
                    // 如果是v2指令，需要验证密钥
                    if ("指令v2".equals(messageType)) {
                        if (parts.length < 5) {
                            getLogger().warning("指令v2格式错误，缺少密钥: " + message);
                            return;
                        }
                        String receivedKey = parts[4];
                        String localKey = config.getString("amer_key", "");
                        if (!receivedKey.equals(localKey)) {
                            getLogger().warning("指令v2密钥验证失败，丢弃指令: " + message);
                            return;
                        }
                    }
                    // 调度到主线程执行命令
                    new BukkitRunnable() {
                        @Override
                        public void run() {
                            getServer().dispatchCommand(getServer().getConsoleSender(), value);
                        }
                    }.runTask(this);
                } else if ("状态".equals(messageType)) {
                    String serverIP = getServer().getIp();
                    int serverPort = getServer().getPort();
                    int onlinePlayers = getServer().getOnlinePlayers().size();
                    int maxPlayers = getServer().getMaxPlayers();
                    String statusMessage = String.format("服务器状态：IP: %s, 端口: %d, 在线人数: %d/%d", serverIP, serverPort, onlinePlayers, maxPlayers);
                    sendEvent("状态", "MC", statusMessage);
                }
            } else {
                getLogger().warning("收到的 token 不匹配，丢弃消息。");
            }
        }
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        sendEvent("玩家加入", player.getName(), "");
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        Player player = event.getPlayer();
        sendEvent("玩家退出", player.getName(), "");
    }

    @EventHandler
    public void onPlayerChat(AsyncPlayerChatEvent event) {
        Player player = event.getPlayer();
        String message = event.getMessage();
        sendEvent("聊天消息", player.getName(), message);
    }

    @EventHandler
    public void onPlayerCommandPreprocess(PlayerCommandPreprocessEvent event) {
        Player player = event.getPlayer();
        String command = event.getMessage();
        sendEvent("玩家命令", player.getName(), command);
    }

    @EventHandler
    public void onPlayerDeath(PlayerDeathEvent event) {
        Player player = event.getEntity();
        String deathMessage = event.getDeathMessage();
        sendEvent("玩家死亡", player.getName(), deathMessage);
    }

    @EventHandler
    public void onPlayerRespawn(PlayerRespawnEvent event) {
        Player player = event.getPlayer();
        sendEvent("玩家重生", player.getName(), "");
    }

    @EventHandler
    public void onServerLoad(ServerLoadEvent event) {
        sendEvent("服务器加载", "服务器", "");
    }
}
