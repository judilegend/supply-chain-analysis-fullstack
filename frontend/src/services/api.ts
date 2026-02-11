import axios from 'axios';

const isDev = import.meta.env.DEV;
const API_BASE_URL = isDev ? 'http://localhost:5000/api' : '/api';

export const getDashboardData = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/dashboard`);
        return response.data;
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        throw error;
    }
};
