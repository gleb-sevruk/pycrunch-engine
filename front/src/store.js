import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    websocket: null,
    file_map: [],
  },
  mutations: {
    socket_did_connect(state, ws) {
      state.websocket = ws
    },
    socket_did_receive_event(state, event) {
      if (event.event_type === 'file_did_load') {
        let file_content = String.fromCharCode.apply(null, new Uint8Array(event.file_contents));
        console.log('file_did_load', event.filename)
        state.file_map.push({filename:event.filename, file_content:file_content})

      }
    },
  },
  getters: {
    getFileByName: (state) => (filename) => {
      let fileMapElement = state.file_map.find(_ => _.filename === filename)

      return fileMapElement
    }
  },
  actions: {
    queue_file_load({state}, filename) {
      state.websocket.emit('my event', {action: 'load-file', filename: filename});
    },
  }
})
