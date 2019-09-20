<template>
  <div class="about">
    <pc-socket-test @pipeline="on_socket_event" @did-connect="run_diagnostics"/>

    <h3>Summary:</h3>
    <template v-if="diagnostics">
      <div class="mb-5">Engine: <span class="badge-light">{{diagnostics.engine}}</span></div>
      <h5>Environment:</h5>

      <div class="envs">
        <div  v-for="e in envs" :key="e.name">
          <div class="envs__single env">
            <div class="env__name">
              {{e.name}}
            </div>
            <div class="env__value">
              {{e.value}}
            </div>
          </div>
        </div>
      </div>
      <h5 class="mt-5">Modules ({{diagnostics.modules.length}} total):</h5>

      <div class="modules">
        <div class="modules__single" v-for="m in diagnostics.modules" :key="m">
          <div class="">{{m}}</div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
  import PcSocket from './PcSocket'
  import config from '@/config'
  import axios from 'axios'
  import {mapState} from 'vuex'

  export default {
    name: 'home',
    data () {

      return {
        diagnostics: null,
      }
    },
    components: {
      'pc-socket-test' : PcSocket,
    },
    async mounted () {
      if (this.websocket) {
        this.run_diagnostics()
      }
    },
    methods: {
      run_diagnostics() {
        this.websocket.emit('my event', {action: 'diagnostics'});
      },
      test_run_completed (data) {
        this.test_run = data.coverage
        // for (let fqn in this.test_run.all_runs) {
        //   let test_in_list = this.discovery_response.tests.find(_ => _.fqn === fqn)
        //   test_in_list.state = 'Completed'
        // }
      },
      on_socket_event (data){
        console.log('pipe', data)
        if (data.event_type === 'diagnostics_did_become_available') {
          this.diagnostics = data
        }
      },

    },
    computed: {
      ...mapState(['websocket']),
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