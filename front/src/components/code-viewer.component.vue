<template>

  <div>
    <div class="file__line" v-for="line in lines" :key="line.index">{{line.state}} {{line.index}} | {{line.text}} </div>

  </div>

</template>

<script>
  export default {
    props: ['file', 'coverage'],
    name: 'pc-code-viewer',
    methods: {
      splitLines (t) {
        return t.split(/\r\n|\r|\n/)
      }
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
</style>