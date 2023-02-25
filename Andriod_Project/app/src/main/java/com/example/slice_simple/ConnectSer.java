package com.example.slice_simple;

import static java.lang.Math.min;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Message;
import android.widget.ImageView;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.Socket;

/**
 * 和渲染服务器通信的线程类，接收视频数据
 */

public class ConnectSer{
    private boolean isSlice = false;
    private ConnectSlice cs = null;
    private final static String SEND_IP = "192.168.1.2";  //发送IP
    private final static int SEND_PORT = 5051;               //发送端口号
    private final static int RECV_POR = 8899;               //接收端口号
    private InetAddress serverAddr;

    private ImageView imgShow;// 图像显示
    private ReceiveHandler receiveHandler = new ReceiveHandler();
    private SendHandler sendHandler = new SendHandler();
    class ReceiveHandler extends Handler {
        @Override
        public void handleMessage(Message msg) {
            super.handleMessage(msg);
            imgShow.setImageBitmap(bp);
        }
    }
    class SendHandler extends Handler {
        @Override
        public void handleMessage(Message msg) {
            super.handleMessage(msg);
        }
    }
    Bitmap bp;


    public void init(ImageView i){
        imgShow = i;
    }
    public void recFile(){
        try {
            serverAddr = InetAddress.getByName(SEND_IP);
            new UdpSendThread().start();
            DatagramSocket socket = new DatagramSocket(RECV_POR);
            while(true) {

                byte[] inBuf= new byte[1024*1024];
                DatagramPacket inPacket = new DatagramPacket(inBuf,inBuf.length);
                //out.write(inPacket.getData());
                socket.receive(inPacket);
                if(!inPacket.getAddress().equals(serverAddr)){
                    throw new IOException("未知名的报文");
                }

                ByteArrayInputStream in = new ByteArrayInputStream(inPacket.getData());
                bp = BitmapFactory.decodeStream(in);//暂时无法播放，寻找新的解码方式
//                System.out.println("Tag:性能测试 成功接收报文" + "内容：" + bp.getWidth());
                receiveHandler.sendEmptyMessage(1);
            }
        }
        catch (IOException e) {
            System.out.println("和渲染服务器通信失败");
            System.out.println(e);
        }
    }

    class UdpSendThread extends Thread{
        @Override
        public void run() {
            try {
                serverAddr = InetAddress.getByName(SEND_IP);
                DatagramSocket socket = new DatagramSocket(RECV_POR - 1); //por-1发送一次，后面用por的接受
                byte[] buf = "i am an android client, hello android! ".getBytes();
                DatagramPacket outPacket = new DatagramPacket(buf, buf.length, serverAddr, SEND_PORT);
                socket.send(outPacket);
                socket.close();
                sendHandler.sendEmptyMessage(1);
            } catch (IOException e) {
                System.out.println("和渲染服务器通信失败");
                System.out.println(e);
            }
        }
    }
}
