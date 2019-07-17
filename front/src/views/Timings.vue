<template>
  <div class="about">
    <pc-socket-test @pipeline="on_socket_event"/>

    <h3>Summary Timings:</h3>
    <template v-if="timings">
      <div class="timing" v-for="timing in timings.results" :key="timing.name">
        <div class="tl-name">{{timing.timeline_name}}</div>
<!--        {{timing}}-->
        <div class="event" v-for="t in timing.intervals" :key="t.name">
          {{t.name}} - Duration - {{t.duration}} seconds
          <h5 class="title">
          Events:
          </h5>
          <div class="evts ml-5" v-for="e in t.events" :key="e.name">
            {{e.name}} - {{e.timestamp}}

          </div>
        </div>

        </div>
    </template>
  </div>
</template>
<script>
  import PcSocket from './PcSocket'
  import config from '@/config'
  import axios from 'axios'

  export default {
    name: 'home',
    data () {

      return {
        timings: null,
      }
    },
    components: {
      'pc-socket-test' : PcSocket,
    },
    async mounted () {
      let url = config.api_url + '/timings'

      try {
        await axios.get(url)
      }
      catch (e) {
        this.$notify.error({title: 'Error', message: e.message + ` at ${url}`, })
      }
    },
    methods: {


      on_socket_event (data){
        console.log('pipe', data)
        if (data.event_type === 'execution_history_did_become_available') {
          this.timings = data
        }
      },

    },
    computed: {
      envs () {
        if (!this.diagnostics) {
          return []
        }
        let res = []
        let env = this.diagnostics.env
        for (let k in env) {
          let target_value = env[k]
          if (k.toLowerCase().indexOf('path') >= 0) {
            target_value = target_value.split(':')
          }
          res.push({name: k, value: target_value})
        }

        return res
      }
    },

  }
</script>
<style scoped>
  .env {
    display: flex;

    flex-direction: row;
  }
  .env__name {
     /*width: 400px;*/
     flex: 1 0 25%
   }
  .env__value {
    /*max-width: 1000px;*/
    flex: 1 0 75%
  }

  .modules {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
  }
  .modules__single {
     width: 500px;
  }
</style>