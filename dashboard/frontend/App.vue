<template>
  <div style="padding: 2rem;">
    <h1>Polymarket Grouped Data Dashboard</h1>
    <button @click="fetchData" :disabled="loading" style="margin-bottom: 1rem;">Refresh</button>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; min-width: 900px;">
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Is Win</th>
            <th>Start Time</th>
            <th>Orders</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(round, idx) in groupedData" :key="round.id">
            <td>{{ idx + 1 }}</td>
            <td>{{ round.title }}</td>
            <td>
              <span :style="{color: round.is_win ? 'green' : 'red', fontWeight: 'bold'}">
                {{ round.is_win ? 'WIN' : 'LOSE' }}
              </span>
            </td>
            <td>{{ formatTime(round.start_time) }}</td>
            <td>
              <table border="1" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                  <tr>
                    <th>Price</th>
                    <th>Time</th>
                    <th>Time to Matched (min)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="order in round.orders" :key="order.price + '-' + order.time">
                    <td>{{ order.price }}</td>
                    <td>{{ formatTime(order.time) }}</td>
                    <td>{{ order.time_to_matched }}</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      groupedData: [],
      loading: false
    }
  },
  methods: {
    async fetchData() {
      this.loading = true;
      try {
        const resp = await fetch('http://localhost:8000/api/grouped-data');
        this.groupedData = await resp.json();
      } catch (e) {
        alert('Failed to fetch data');
      }
      this.loading = false;
    },
    formatTime(ts) {
      if (!ts) return '';
      const d = new Date(ts * 1000);
      return d.toLocaleString();
    }
  },
  mounted() {
    this.fetchData();
  }
}
</script>

<style>
body {
  font-family: Arial, sans-serif;
}
</style>
