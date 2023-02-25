package com.example.slice_simple;

/**
 * 模拟的，代表用户信息和用户游戏类型的类。最好是接上云游戏应用来对接。
*/

import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public class SimUserGame {
    public final static int REQ_DEFAULT = 0;
    public final static int REQ_BANDWIDTH = 1;    //要求高带宽（画质）
    public final static int REQ_DELAY = 2;        //低时延和低抖动（操作类）
    public final static int REQ_MOBA = 3;         //高带宽低时延低抖动（竞技且高画质）

    public int gameType = REQ_DEFAULT;
    //以下两个类型的信息先不用，待真正测试时接入用户信息接口再考虑
    private int userLevel = 0;//可以用于标识用户切片套餐等级/会员等级 暂时用不上
    private String userid = null;
    private Map<String, Integer> game_req = new HashMap<>();

    public int state = 0;//表示是否真的发起了切片。即当前切片状态。

    public SimUserGame(){//考虑写到配置文件里
        game_req.put("moba", REQ_MOBA);
        game_req.put("fps", REQ_MOBA);
        game_req.put("msc", REQ_MOBA);
        game_req.put("rcg", REQ_MOBA);
        game_req.put("spg", REQ_MOBA);//体育竞技
        game_req.put("act", REQ_DELAY);//动作
        game_req.put("avg", REQ_DELAY);//冒险
        game_req.put("rpg", REQ_BANDWIDTH);//角色扮演
    }

    public void setGameType(String Game) {
        String game = Game.toLowerCase();
        if(game_req.containsKey(game)){
            gameType = game_req.get(game);
        }
    }

    public void setUser(String uid, int ul){
        if(uid != null)
        {
            userid = uid;
        }
        userLevel = ul;
    }

    public int getGameType() {
        return gameType;
    }

    public int getUserLevel() {
        return userLevel;
    }

    public String getUserid() {
        return userid;
    }
}
