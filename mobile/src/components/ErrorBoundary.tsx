import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error?: Error }> {
  state: { error?: Error } = {};
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error) { console.warn('CitriSurksha UI error', error); }
  render() {
    if (this.state.error) {
      return <View style={styles.wrap}><Text style={styles.title}>Something went wrong</Text><Text style={styles.msg}>{this.state.error.message}</Text><Pressable style={styles.btn} onPress={() => this.setState({ error: undefined })}><Text style={styles.btnText}>Try again</Text></Pressable></View>;
    }
    return this.props.children;
  }
}
const styles = StyleSheet.create({ wrap:{flex:1,alignItems:'center',justifyContent:'center',padding:24,backgroundColor:'#f8fff3'}, title:{fontSize:22,fontWeight:'900',color:'#b00020'}, msg:{textAlign:'center',marginVertical:12,color:'#40513d'}, btn:{backgroundColor:'#116530',padding:14,borderRadius:12}, btnText:{color:'white',fontWeight:'900'} });
