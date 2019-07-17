<template>
  <div id="app">
    <h2 class="text-center mt-4">PyCrunch</h2>

    <div id="nav" class="text-center">
      <router-link to="/">Main</router-link> |
      <router-link to="/more">Diagnostics</router-link> |
      <router-link to="/timings">Timings</router-link>
    </div>
    <router-view/>
  </div>
</template>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
#nav {
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
