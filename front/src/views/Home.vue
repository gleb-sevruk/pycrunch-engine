<template>
  <div class="home">
    <div class="file">{{entry_file}}</div>
    <el-button @click="run_coverage()">Run</el-button>
    <div class="test-run">
      {{test_run}}
      <div class="all-files" v-if="test_run" >
        <div class="test-run__file mt-4" v-for="file in test_run.results.files" :key="file.filename">
          {{file.filename}}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import axios from 'axios'
import config from '@/config'
export default {
  name: 'home',
  data () {
    return {
      entry_file: '',
      test_run: null,
    }
  },
  components: {
  },
  async mounted () {
    let x = await axios.get(config.api_url + '/entry-file')
    this.entry_file = x.data.entry_file
  },
  methods: {
    async run_coverage () {
      let x = await axios.post(config.api_url + '/coverage')
      this.test_run = x.data
    },
  },

}
</script>
