package com.example.slice_simple;

import android.content.Context;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayDeque;
import java.util.ArrayList;

/**
 * 读取模拟的NetDelay.txt中数据，即[BANDWIDTH, 丢包率, 时延] 单位为Mbps, %, ms。
 */
public class SimBDPGen {
    private static SimBDPGen INSTANCE = null;
    private ArrayList<ArrayDeque<Double>> content = null;

    public static SimBDPGen getInstance(){
        if(INSTANCE == null){
            INSTANCE = new SimBDPGen();
        }
        return INSTANCE;
    }

    /**
     * @param context
     * @return [ [带宽], [丢包率], [时延] ]
     * 从文件中读取的数据
     */

    public ArrayList<ArrayDeque<Double>> getContent(Context context) {
        if(content != null){
            return content;
        }
        InputStream is = null;
        content = new ArrayList<>();
        ArrayDeque<Double> band = new ArrayDeque<>();
        ArrayDeque<Double> ji = new ArrayDeque<>();
        ArrayDeque<Double> pl = new ArrayDeque<>();
        ArrayDeque<Double> delay = new ArrayDeque<>();
        try {
            is = context.getResources().getAssets().open("NetDelay.txt");
            BufferedReader reader = new BufferedReader(new InputStreamReader(is));
            String line;
            while((line = reader.readLine()) != null){// [带宽,丢包率,时延]
                int idx = line.indexOf(',');
                double b = Double.parseDouble(line.substring(0, idx));
                if(band.size() != 0){
                    double j = band.getLast() - b;
                    if (j < 0) j = -j;
                    ji.add(j);
                }
                band.add(b);

                line = line.substring(idx + 1);
                idx = line.indexOf(',');
                pl.add(Double.parseDouble(line.substring(0, idx)) );

                line = line.substring(idx + 1);
                delay.add(Double.parseDouble(line));
            }
            content.add(band);
            content.add(delay);
            content.add(ji);
            content.add(pl);
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
        return content;
    }
}