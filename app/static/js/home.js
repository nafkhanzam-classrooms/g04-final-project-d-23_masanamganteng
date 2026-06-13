(() => {
  const roomList = document.getElementById('roomList');
  const status = document.getElementById('wsStatus');
  const ws = new WebSocket(JT.wsUrl('/ws/home'));
  ws.addEventListener('open', () => status.textContent = 'online');
  ws.addEventListener('close', () => status.textContent = 'offline');
  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'ROOM_LIST_UPDATE') renderRooms(msg.payload.rooms || []);
  });
  setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send('ping'); }, 5000);

  function renderRooms(rooms) {
    if (!rooms.length) {
      roomList.className = 'room-list empty';
      roomList.textContent = 'Belum ada room tersedia.';
      return;
    }
    roomList.className = 'room-list';
    roomList.innerHTML = rooms.map(room => `
      <div class="room-item">
        <div>
          <strong>Room ${room.room_id}</strong>
          <div class="room-meta">
            <span>Pembuat: ${escapeHtml(room.creator_name)}</span>
            <span>Tipe: ${room.game_type}</span>
            <span>Kapasitas: ${room.current_players}/${room.max_players}</span>
          </div>
        </div>
        <a class="btn btn-primary" href="/room/${room.room_id}?join=1">Gabung</a>
      </div>`).join('');
  }
  function escapeHtml(value) {
    return String(value).replace(/[&<>"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
  }
})();
