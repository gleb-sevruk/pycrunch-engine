<template>
  <div class="home">
    <hr/>
    <pc-socket-test @pipeline="on_pipeline"/>
    <div class="files ml-5">
      <div class="text-secondary">Discovered tests:</div>
      <template v-if="discovery_response">
        <div class="files__single" v-for="module in discovery_response.modules" :key="module.filename">
          <code class="text-info">{{module.filename}}</code>
          <div class="test-methods">
            <div class="test-methods ml-4" v-for="test in module.tests_found" :key="test">
              <div class="single__test d-flex mt-2">
                <div class="alert-success px-2">+</div>
                <div class="single-test__name ml-2">{{test}}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
<!--    <el-button @click="run_coverage()">Run</el-button>-->
    <div class="test-run ml-3">
<!--      {{test_run}}-->
      <div class="all-files" v-if="test_run" >
        <div class="test-run__file mt-4" v-for="(run, index) in test_run.all_runs" :key="run.entry_point">
          <code>{{index + 1}} {{run.entry_point}}</code>
          <div class="test-run__file mt-4" v-for="file in run.files" :key="file.filename">
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
  import PcSocketTest from './PcSocketTest'

  export default {
  name: 'home',
  data () {
    return {
      folder: '/Users/gleb/code/PyCrunch/',
      entry_files: [],
      test_run: null,
      file_contents: null,
      discovery_response: null,
    }
  },
  components: {
    'pc-socket-test' : PcSocketTest,
    'pc-code-viewer' : CodeViewer,
  },
  async mounted () {
    let url = config.api_url + '/discover'

    try {
      let x = await axios.get(url, {params: {folder: this.folder}})
      this.discovery_response = x.data
      x = await this.run_coverage()
    }
    catch (e) {
      this.$notify.error({title: 'Error', message: e.message + ` at ${url}`, })
    }
  },
  methods: {
    async run_coverage () {
      let x = await axios.post(config.api_url + '/coverage', {entry_files: [ '/Users/gleb/code/PyCrunch/tests.py',
          '/Users/gleb/code/PyCrunch/playground.py',]})
      this.test_run = x.data
    },
    on_pipeline (data){
      console.log('pipe', data)
      this.run_coverage()
    },

  },
  computed: {

  },

}
</script>
<style scoped>
.files {

}
</style>