<template>

  <div v-loading="loading">
    <div class="file__line" :class="{'line-state__green' : line.state === '+'}" v-for="line in lines" :key="line.index"><span class="file__line-number">{{line.state}} {{line.index}}</span>{{line.text}} </div>

  </div>

</template>

<script>
  import {mapActions, mapGetters} from 'vuex'

  export default {
    props: ['filename', 'coverage'],
    name: 'pc-code-viewer',
    data () {
      return {
        loading: true,
      }
    },
    updated () {
      if (!this.getFileByName(this.filename)) {
        this.load_file()
      }

    },

    async mounted() {
      console.log('this.file', this.file)
      await this.load_file()
      this.loading = false

    },
    methods: {
      ...mapActions(['queue_file_load']),
      async load_file() {
        this.queue_file_load(this.filename)

        // let x = await axios.get(config.api_url + '/file', {params: {file: this.filename}})
        // this.file = x.data
      },
      splitLines (t) {
        if (!t) {
          return []
        }
        return t.split(/\r\n|\r|\n/)
      },
      async download_file (filename) {
        this.queue_file_load(filename)
        // let x = await axios.get(config.api_url + '/file', {params: {file:filename}})
        // return x.data
      },
    },
    computed: {
      ...mapGetters(['getFileByName']),
      lines () {
        let file = this.getFileByName(this.filename)
        if (!file) {
          return []
        }
        console.log('file', file)
        file = file.file_content
        let splited = this.splitLines(file)
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