// userHandler.js
// Defines event handlers for a socket connected to a user.
// This module should be required to register those event handlers.

const { roomList } = require("../lib/global");
const { getMediasoupWorker } = require("../lib/Worker");
const Room = require("../lib/Room");
const Peer = require("../lib/Peer");
var fs = require('fs');
const { getLastLine } = require("../../moderator/fileTools");

module.exports = function (io, socket) {
  socket.on("createRoom", async ({ room_id }, callback) => {
    if (roomList.has(room_id)) {
      callback("already exists");
    } else {
      console.log("---created room--- ", room_id);
      let worker = await getMediasoupWorker();
      roomList.set(room_id, new Room(room_id, "random name", worker, io));
      callback(room_id);
    }
  });

  socket.on("saveLog", ({ room_name, user_name, userLog }) => {
    const dir = 'logs/' + room_name + '_' + socket.room_id;

    for (var timestamp in userLog) {
      fs.appendFile(dir + '/' + user_name + '.txt', userLog[timestamp], function (err) {
        if (err) console.log(err);
        console.log('[Log(' + user_name + ')] ', new Date(Number(timestamp)).toTimeString().split(' ')[0], userLog[timestamp].trim().split(') ')[1]);
      });
    }
  });

  socket.on("saveSubtask", ({ room_name, user_name, subtaskLog }) => {
    const dir = 'logs/' + room_name + '_' + socket.room_id + '/subtask';

    for (var timestamp in subtaskLog) {
      fs.appendFile(dir + '/subtask_monitoring.txt', user_name + " :\t" + subtaskLog[timestamp].trim().split(') ')[1] + "\n", function (err) {
        if (err) console.log(err);
      });
      fs.appendFile(dir + '/subtask_' + user_name + '.txt', subtaskLog[timestamp], function (err) {
        if (err) console.log(err);
        // console.log('[Log(' + user_name + ')] ', new Date(Number(timestamp)).toTimeString().split(' ')[0], 'SUBTASK-SAVED/CONTENT=' + subtaskLog[timestamp].trim().split(') ')[1]);
      })
    }
  });

  socket.on("noteUpdateLog", ({ room_name, user_name, content, updateTimestamp }) => {
    let logContent = '(' + updateTimestamp + ') ' + content + '\n';

    const dir = 'logs/' + room_name + '_' + socket.room_id;
    fs.appendFile(dir + '/' + user_name + '_notepad.txt', logContent, function (err) {
      if (err) console.log(err);
      // console.log('[NotePad] log saved at ', updateTimestamp);
    });
  });

  socket.on("join", ({ room_id, room_name, name }, cb) => {
    console.log('---user joined--- "' + room_id + '": ' + name);
    if (!roomList.has(room_id)) {
      return cb({
        error: "room does not exist",
      });
    }

    // Construct new log file for user
    let msg = '(' + Date.now() + ') User ' + name + ' joined.\n';
    msg = msg + '                [roomID] ' + room_id + '\n';
    msg = msg + '                [roomName] ' + room_name + '\n';
    msg = msg + '                [userName] ' + name + '\n';
    msg = msg + '                [socketID] ' + socket.id + '\n';

    // Check if room dir exist and make if not exist.
    const dir = 'logs/' + room_name + '_' + room_id;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, {
        recursive: true
      });
    }

    // undifiend dir for handle undifined error
    const dir_un = 'logs/' + room_name + '_undefined';
    if (!fs.existsSync(dir_un)) {
      fs.mkdirSync(dir_un, {
        recursive: true
      });
    }

    fs.appendFile(dir + '/' + name + '.txt', msg, function (err) {
      if (err) console.log(err);
      console.log('Log file for user ', name, ' is created successfully.');
    });

    fs.appendFile(dir + '/' + room_name + '.txt', msg, function (err) {
      if (err) console.log(err);
      console.log('Log file for room is created successfully.');
    });

    // Check if subtask log dir exist and make if not exist.
    const stdir = dir + '/subtask';
    if (!fs.existsSync(stdir)) {
      fs.mkdirSync(stdir, {
        recursive: true
      });
    }

    // undifiend dir for handle undifined error
    const dir_un_subtask = 'logs/' + room_name + '_undefined/subtask';
    if (!fs.existsSync(dir_un_subtask)) {
      fs.mkdirSync(dir_un_subtask, {
        recursive: true
      });
    }

    fs.appendFile(stdir + '/subtask_' + name + '.txt', msg, function (err) {
      if (err) console.log(err);
      console.log('Log file for subtask of user ', name, ' is created successfully.');
    });

    let room = roomList.get(room_id);
    if (room.roomExpireTimeout) {
      clearTimeout(room.roomExpireTimeout);
      room.roomExpireTimeout = null;
    }

    room.addPeer(new Peer(socket.id, name));
    socket.room_id = room_id;

    cb(roomList.get(room_id).toJson());
  });

  socket.on("getProducers", () => {
    // send all the current producer to newly joined member
    if (!roomList.has(socket.room_id)) return;

    console.log(
      `---get producers--- name:${roomList.get(socket.room_id).getPeers().get(socket.id).name
      }`
    );

    let producerList = roomList
      .get(socket.room_id)
      .getProducerListForPeer(socket.id);

    socket.emit("newProducers", producerList);
  });

  socket.on("getRouterRtpCapabilities", (_, callback) => {
    if (!roomList.has(socket.room_id)) return;
    console.log(
      `---get RouterRtpCapabilities--- name: ${roomList.get(socket.room_id).getPeers().get(socket.id).name
      }`
    );
    try {
      callback(roomList.get(socket.room_id).getRtpCapabilities());
    } catch (e) {
      callback({
        error: e.message,
      });
    }
  });

  socket.on("createWebRtcTransport", async (_, callback) => {
    if (!roomList.has(socket.room_id)) return;
    try {
      const { params } = await roomList
        .get(socket.room_id)
        .createWebRtcTransport(socket.id);

      console.log(
        `---create webrtc transport--- name: ${roomList.get(socket.room_id).getPeers().get(socket.id).name
        }`
      );

      callback(params);
    } catch (err) {
      console.error(err);
      callback({
        error: err.message,
      });
    }
  });

  socket.on(
    "connectTransport",
    async ({ transport_id, dtlsParameters }, callback) => {
      if (!roomList.has(socket.room_id)) return;
      console.log(
        `---connect transport--- name: ${roomList.get(socket.room_id).getPeers().get(socket.id).name
        }`
      );

      await roomList
        .get(socket.room_id)
        .connectPeerTransport(socket.id, transport_id, dtlsParameters);

      callback("success");
    }
  );

  socket.on(
    "produce",
    async ({ kind, rtpParameters, producerTransportId }, callback) => {
      if (!roomList.has(socket.room_id)) {
        return callback({ error: "not is a room" });
      }

      let producer_id = await roomList
        .get(socket.room_id)
        .produce(socket.id, producerTransportId, rtpParameters, kind);
      console.log(
        `---produce--- type: ${kind} name: ${roomList.get(socket.room_id).getPeers().get(socket.id).name
        } id: ${producer_id}`
      );
      callback({
        producer_id,
      });
    }
  );

  socket.on(
    "consume",
    async ({ consumerTransportId, producerId, rtpCapabilities }, callback) => {
      if (!roomList.has(socket.room_id)) return;

      let params = await roomList
        .get(socket.room_id)
        .consume(socket.id, consumerTransportId, producerId, rtpCapabilities);

      if (!params) {
        console.log("!!!Params Error!!!");
        return;
      }

      console.log(
        `---consuming--- name: ${roomList.get(socket.room_id) &&
        roomList.get(socket.room_id).getPeers().get(socket.id).name
        } prod_id:${producerId} consumer_id:${params.id}`
      );
      callback(params);
    }
  );

  socket.on("getMyRoomInfo", (_, cb) => {
    cb(roomList.get(socket.room_id).toJson());
  });

  socket.on("disconnect", () => {
    if (!roomList.has(socket.room_id)) return;
    let room = roomList.get(socket.room_id);
    console.log(
      `---disconnect--- name: ${room &&
      room.getPeers().get(socket.id).name
      }`
    );
    if (!socket.room_id) return;
    if (!roomList.has(socket.room_id)) return;

    const dir = 'logs/' + room.name + '_' + socket.room_id;
    let logfile = dir + '/' + room.getPeers().get(socket.id).name + '.txt';
    fs.appendFile(logfile, '(' + Date.now() + ') Exit\n', function (err) {
      if (err) console.log(err);
      console.log('[Log] Add Disconnect Log');
    });
    room.removePeer(socket.id);

    if (room.getPeers().size === 0) {
      if (room.roomExpireTimeout) {
        clearTimeout(room.roomExpireTimeout);
      }
      room.roomExpireTimeout = setTimeout(() => {
        if (room.router) {
          room.router.close();
          room.router = null;
        }
        room.roomExpireTimeout = null;

        roomList.delete(room.id);
        console.log(`DESTROYED: ${room.id} after timeout`);
      }, 30 * 1000);
    }

    socket.room_id = null;
  });

  socket.on("producerClosed", ({ producer_id }) => {
    if (!roomList.has(socket.room_id)) return;
    console.log(
      `---producer close--- name: ${roomList.get(socket.room_id) &&
      roomList.get(socket.room_id).getPeers().get(socket.id).name
      }`
    );

    roomList.get(socket.room_id).closeProducer(socket.id, producer_id);
  });

  socket.on("exitRoom", async (_, callback) => {
    if (!roomList.has(socket.room_id)) {
      callback({
        error: "not currently in a room",
      });
      return;
    }

    console.log(
      `---exit room--- name: ${roomList.get(socket.room_id) &&
      roomList.get(socket.room_id).getPeers().get(socket.id).name
      }`
    );

    // close transports
    let room = roomList.get(socket.room_id);
    await room.removePeer(socket.id);

    if (roomList.get(socket.room_id).getPeers().size === 0) {
      if (room.roomExpireTimeout) {
        clearTimeout(room.roomExpireTimeout);
        room.roomExpireTimeout = null;
      }
      if (room.router) {
        room.router.close();
        room.router = null;
      }

      roomList.delete(socket.room_id);
      console.log(`DESTROYED: ${socket.room_id} after timeout`);
    }

    socket.room_id = null;

    callback("successfully exited room");
  });
};

function room() {
  return Object.values(roomList).map((r) => {
    return {
      router: r.router.id,
      peers: Object.values(r.peers).map((p) => {
        return {
          name: p.name,
        };
      }),
      id: r.id,
    };
  });
}
