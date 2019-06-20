<template>
  <div class="socket-test"></div>
</template>
<script>
  import config from '../config'
  import io from 'socket.io-client';

  export default {
    name: 'pc-socket-test',
    mounted () {
      let socket = io.connect(config.api_url);
      socket.on('connect', () => {
        console.log('WS connect')

        socket.emit('my event', {data: 'I\'m connected!'});
        socket.emit('json', {data: 'I\'m connected!'});
      });

      socket.on('event', data => {
        // console.log('WS Event', data)
        this.$emit('pipeline', data)
      });
      socket.on('disconnect', () => {
        console.log('WS disconnect')
      });
    }
  }
</script>
