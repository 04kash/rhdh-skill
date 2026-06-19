const http = require('http');

const port = process.env.PORT || 3000;

const server = http.createServer((_req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ service: '{{ values.componentId }}', status: 'ok' }));
});

server.listen(port, () => {
  console.log(`{{ values.componentId }} listening on port ${port}`);
});
