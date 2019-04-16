<template>
  <div class="home">
    <hr/>
    <pc-socket-test @pipeline="on_pipeline"/>
    <div class="files ml-5">
      <div class="text-secondary">Entry points:</div>
      <div class="files__single" v-for="file in entry_files" :key="file">
        {{file}}
      </div>
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
      entry_files: [],
      test_run: null,
      file_contents: null,
    }
  },
  components: {
    'pc-socket-test' : PcSocketTest,
    'pc-code-viewer' : CodeViewer,
  },
  async mounted () {
    let url = config.api_url + '/entry-files'

    try {
      let x = await axios.get(url)
      this.entry_files = x.data.entry_files
      x = await this.run_coverage()
    }
    catch (e) {
      this.$notify.error({title: 'Error', message: e.message + ` at ${url}`, })
    }
  },
  methods: {
    async run_coverage () {
      let x = await axios.post(config.api_url + '/coverage', {entry_files: this.entry_files})
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