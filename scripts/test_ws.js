
const WebSocket = require('ws');

const url = 'wss://receptionist.lexmakesit.com/twilio/stream';
console.log(`Connecting to ${url}...`);

const ws = new WebSocket(url);

ws.on('open', function open() {
    console.log('Connected!');
    ws.close();
});

ws.on('error', function error(err) {
    console.log('Error:', err.message);
});

ws.on('close', function close() {
    console.log('Closed');
});
