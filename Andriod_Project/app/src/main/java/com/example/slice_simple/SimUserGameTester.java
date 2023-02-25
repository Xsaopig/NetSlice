package com.example.slice_simple;

import java.util.Map;
import java.util.Random;

/**
 * 随机生成SimUserGame的类。
 */
public class SimUserGameTester {
    public static String[] dir = {"rpg", "act", "avg", "moba", "fps", "msc", "rcg", "spg"};
    private static SimUserGameTester INSTANCE = new SimUserGameTester();

    private SimUserGameTester(){

    }

    public SimUserGame generate(){
        //随机数产生
        Random rand = new Random();
        int gt = rand.nextInt(8);
        int ul = rand.nextInt(3);
        return generate(dir[gt], "000000", ul);
    }

    public SimUserGame generate(String Game, String uid, int uLevel){
        SimUserGame sug = new SimUserGame();
        sug.setGameType(Game);
        sug.setUser(uid, uLevel);
        return sug;
    }

    public static SimUserGameTester getINSTANCE(){
        return INSTANCE;
    }
}
