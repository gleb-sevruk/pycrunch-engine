<template>
  <div class="home">
    <hr/>
    <pc-socket-test @pipeline="on_socket_event" @did-connect="run_discovery"/>
    <el-tag v-if="!websocket" type="danger" class="ml-5">No socket connection</el-tag>
    <el-tag v-if="websocket" type="success" class="ml-5">Connected to websocket</el-tag>
    <div class="files ml-5">
      <div class="text-secondary mb-4">Discovered tests:</div>
      <template v-if="discovery_response">
        <div class="files__single" v-for="test in discovery_response.tests" :key="test.fqn">
          <div class="test-methods">
              <div class="single__test d-flex mt-2" @click="run_test(test)">
                <div class=" px-2 pointer text-capitalize single-test__badge" :class="class_from_state(test)"> {{test.state}} </div>
                <div class="single-test__name ml-2">{{test.module}} - <span class="text-info">{{test.name}}</span></div>
              </div>
          </div>
        </div>
        <el-button class="mt-5" @click="run_all_tests()">Run all</el-button>
      </template>
    </div>
    <div class="test-run ml-3">
      <el-checkbox v-model="show_more">Show more detailed information</el-checkbox>
      <div v-if="show_more">
      <pre>{{combined_coverage2}}</pre>


      {{test_run}}
      </div>
      <div class="all-files" v-if="test_run" >
        <div class="test-run__file mt-4" v-for="run in test_run.all_runs" :key="run.entry_point">
          <code>{{run.time_elapsed}}ms | {{run.entry_point}}</code>
          <div class="terminal-output">{{run.captured_output}}</div>
          <div class="test-run__file mt-4 pb-5" v-for="file in run.files" :key="file.filename">
            <div class="file-name">{{file.filename}}</div>
            <pc-code-viewer :filename="file.filename" :coverage="file.lines_covered"></pc-code-viewer>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  // @ is an alias to /src
  import axios from 'axios'
  import config from '@/config'
  import CodeViewer from '../components/code-viewer.component'
  import PcSocket from './PcSocket'
  import {mapState} from 'vuex'

  export default {
  name: 'home',
  data () {
    return {
      entry_files: [],
      test_run: null,
      combined_coverage: null,
      combined_coverage2: null,
      file_contents: null,
      dependencies: null,
      discovery_response: null,
      show_more: false,
    }
  },
  components: {
    'pc-socket-test' : PcSocket,
    'pc-code-viewer' : CodeViewer,
  },
  async mounted () {
    // let discovery_url = config.api_url + '/discover'
    //
    // try {
    //   let x = await axios.get(discovery_url, {params: {folder: this.folder}})
    //   this.discovery_response = x.data
    //   // x = await this.run_coverage()
    // }
    // catch (e) {
    //   this.$notify.error({title: 'Error', message: e.message + ` at ${discovery_url}`, })
    // }
    if (this.websocket) {
      this.run_discovery()
    }
  },
  methods: {
    run_discovery() {
      console.log('discovery posting!')
      console.log('ws is: ', this.websocket)
      this.websocket.emit('my event', {action: 'discovery'});
    },
    file_modification_event: function (data) {
      let file = data.modified_file
      let dependent_tests = this.dependencies[file]
      if (dependent_tests) {
        // should be handled on engine
      }
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
      if (data.event_type === 'discovery_did_become_available') {
        this.discovery_response = data
      }
      if (data.event_type === 'file_modification') {
        this.file_modification_event(data)
      }
      if (data.event_type === 'test_run_completed') {
        this.test_run_completed(data)
      }
      if (data.event_type === 'combined_coverage_updated') {

        this.combined_coverage = data.combined_coverage
        this.combined_coverage2 = JSON.stringify(data, null, 4);

        this.dependencies = data.dependencies
      }

    },
    async run_test (test) {
      await this.run_specified_tests([test ])
    },
    async run_all_tests () {
       await this.run_specified_tests(this.get_all_tests())

    },
    async run_specified_tests (tests) {
      this.websocket.emit('my event',
        {
          action: 'run-tests',
          tests: tests,
        });
      // await axios.post(config.api_url + '/run-tests', { tests })

    },
    get_all_tests () {
      // let xx = this.discovery_response.modules.flatMap(_ => _.tests_found)
      let xx = this.discovery_response.tests
      return xx
    },
    class_from_state (test) {
      if (test.state === 'pending') {
        return 'alert-secondary'
      }
      if (test.state === 'success') {
        return 'alert-success'
      }
      if (test.state === 'failed') {
        return 'alert-danger'
      }


      return 'badge-warning'
    }
  },
  computed: {
    ...mapState(['websocket']),

  },

}
</script>
<style scoped>
.files {

}

  .pointer {
    cursor: pointer;
  }

  .single-test__badge {
    width: 6em;
    text-align: center;
  }
  .terminal-output{
    white-space: pre;
    background-color: #292c2f;
    font-family: monospace;
    color: white;
  }
</style>