const https = require("https");
const fs = require("fs");
const path = require("path");
const config = require("./config");

// SSL parameters
const options = {
  key: fs.readFileSync(path.join(__dirname, config.sslKey), "utf-8"),
  cert: fs.readFileSync(path.join(__dirname, config.sslCrt), "utf-8"),
};

const httpsServer = https.createServer(options);
const io = require("socket.io")(httpsServer, {
  cors: {
    origin: config.mediaServerHost,
  },
  maxHttpBufferSize: 1e8
});

const Clerk = require("./Clerk");
const { clerks } = require("./global");

// Use audioFileHandler.js for en-US transcript
const registerSpeechHandler = require("./audioFileHandler");

io.on("connection", async (socket) => {
  const { room_id, room_name, user_name } = socket.handshake.query;
  if (room_id) {
    await socket.join(room_id);
    if (!clerks.has(room_id)) {
      clerks.set(room_id, new Clerk(io, room_id, room_name));
      console.log(`Room created: ${room_name} (${room_id})`);
    }

    socket.room_id = room_id;
    socket.user_name = user_name;
    console.log(`${user_name} joined ${room_name} (${room_id}) on moderator server`);

    // Reload past conversations if exist
    await clerks.get(socket.room_id).restoreParagraphs();

    await registerSpeechHandler(io, socket);
  } else {
    socket.disconnect(true);
  }
});

io.of("/").adapter.on("delete-room", (room_id) => {
  if (clerks.has(room_id)) {
    //// let clerk = clerks.get(room_id);
    //// clerk.clearSwitchTimeout();
    clerks.delete(room_id);
    console.log(`Room deleted: ${room_id}`);
  }
});

httpsServer.listen(config.listenPort, () => {
  console.log(`moderator server listening https ${config.listenPort}`);
});
