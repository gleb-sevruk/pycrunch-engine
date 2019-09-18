<template>
  <div class="socket-test"></div>
</template>
<script>
  import config from '../config'
  import io from 'socket.io-client';
  import {mapMutations, mapState} from 'vuex'

  export default {
    name: 'pc-socket-test',
    methods: {
      ...mapMutations(['socket_did_connect', 'socket_did_receive_event'])
    },
    mounted () {
      let socket = io.connect(config.api_url);
      socket.on('connect', () => {
        console.log('WS connect')
        this.socket_did_connect(socket)
        this.$emit('did-connect', {})

        socket.emit('my event', {data: 'I\'m connected!'});
        socket.emit('json', {data: 'I\'m connected!'});
      });

      socket.on('event', data => {
        // console.log('WS Event', data)
        this.socket_did_receive_event(data)
        this.$emit('pipeline', data)
      });
      socket.on('disconnect', () => {
        console.log('WS disconnect')
      });
    },
    computed: {
      ...mapState(['websocket']),
    },
  }
</script>
