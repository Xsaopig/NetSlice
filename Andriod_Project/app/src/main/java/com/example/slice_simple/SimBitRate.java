package com.example.slice_simple;

import android.content.Context;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * 通过机型的默认支持分辨率，模拟用户游戏分辨率（码率）需求。基于码率对应用需求调整，得到更精准的用户需求。
 * 真实环境中可以直接获取用户当前设置的分辨率。
 * 目前由于实验需求直接设置，本质上用不上这个类。
 */

public class SimBitRate {
    private static Context mContext = null;
    private static volatile SimBitRate INSTANCE = null;
    private Map<String, String> dir= new HashMap<String, String>();

    public static void init_BitRate(Context context){
        mContext = context;
    }

    /**
     *  构造时需从txt文件建立对应机型到码率大小的dir，这就要求mContext非空，即先初始化。
     *  建立dir，机型作为key，码率作为value
     */
    private SimBitRate(){
        if(null == mContext){
            System.out.println("Error in construct BitRate, please init first!");
        }
        ArrayList<String> config = readTextString(mContext);
        for(String tmp:config){
            int idx1 = tmp.indexOf(',');
            int idx2 = tmp.indexOf(',', idx1 + 1);
            dir.put(tmp.substring(0, idx1), tmp.substring(idx2 + 1));
        }
//        for(Map.Entry<String, String> entry: dir.entrySet()){
//            System.out.println("key = " +  entry.getKey() + " and value = " + entry.getValue());
//        }
    }

    public static SimBitRate getInstance(){
        if(INSTANCE == null){
            INSTANCE = new SimBitRate();
        }
        return INSTANCE;
    }


    /**
     * 读取配置机型和码率的txt文件
     */
    private static ArrayList<String> readTextString(Context context) {
        InputStream is = null;
        ArrayList<String> mLines = new ArrayList<>();
        try {
            is = context.getResources().getAssets().open("model.txt");
            BufferedReader reader = new BufferedReader(new InputStreamReader(is));
            String line;
            while((line = reader.readLine()) != null){
                mLines.add(line);
            }
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        finally {
            try {
                is.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return mLines;
    }
    /**
     * 构造时需从txt文件建立对应机型到码率大小的dir，这就要求mContext非空，即先初始化。
    */
    public int getRate(String device){
        if(dir == null){
            System.out.println("Error in getRate, dir is empty! please init first!");
            return -1;
        }
        else{
            String rate = dir.get(device);
            if(rate == null){//文件里没有，则默认为6144kbps码率，即不根据设备调整用户需求
                return 6 * 1024;
            }
            for(int i = 0; i < rate.length(); ++i){
                if(!Character.isDigit(rate.charAt(i))){
                    System.out.println("Error in getRate, rate is not a digit!");
                    return -1;
                }
            }
            return Integer.parseInt(rate);
        }
    }
}
