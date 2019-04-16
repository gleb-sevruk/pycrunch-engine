<template>

  <div v-loading="loading">
    <div class="file__line" :class="{'line-state__green' : line.state === '+'}" v-for="line in lines" :key="line.index"><span class="file__line-number">{{line.state}} {{line.index}}</span>{{line.text}} </div>

  </div>

</template>

<script>
  import axios from 'axios'
  import config from '../config'

  export default {
    props: ['filename', 'coverage'],
    name: 'pc-code-viewer',
    data () {
      return {
        file: null,
        loading: true,
      }
    },
    updated () {
      this.load_file()

    },

    async mounted() {
      console.log('this.file', this.file)
      await this.load_file()
      this.loading = false

    },
    methods: {
      async load_file() {
        let x = await axios.get(config.api_url + '/file', {params: {file: this.filename}})
        this.file = x.data
      },
      splitLines (t) {
        if (!t) {
          return []
        }
        return t.split(/\r\n|\r|\n/)
      },
      async download_file (filename) {
        let x = await axios.get(config.api_url + '/file', {params: {file:filename}})
        return x.data
      },
    },
    computed: {
      lines () {
        if (!this.file) {
          return []
        }
        let splited = this.splitLines(this.file)
        let my_map = splited.map((line, index) => {
          let line_number = index + 1
          let state = '-'
          if (this.coverage.includes(line_number)) {
            state = '+'
          }
          return ({
            index: line_number,
            state,
            text: line
          })
        })
        return my_map
      }
    },
  }
</script>

<style scoped>
  .file__line {
    white-space: pre;
    font-family: monospace;
    text-align: left;
    width: 600px;
    margin: 0 auto;
  }
  .file__line-number {
    display: inline-block;
    width: 50px;
    user-select: none;
    border-right: 1px solid #6c757d;
    margin-right: 1em;

  }
  .line-state__green {
    background-color: rgba(44, 176, 0, 0.2);
  }
</style>