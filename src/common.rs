// core.rs --- 
// 
// Filename: core.rs
// Author: Louise <louise>
// Created: Wed Dec  6 14:34:12 2017 (+0100)
// Last-Updated: Thu Dec 21 22:22:04 2017 (+0100)
//           By: Louise <louise>
// 

pub enum Console {
    Gameboy,
    None
}

#[derive(Debug, Clone, Copy)]
pub struct Color(pub u8, pub u8, pub u8);

#[derive(Debug, Clone, Copy)]
pub enum Key {
    A,
    B,
    Start,
    Select,

    Up,
    Down,
    Right,
    Left
}

#[derive(Debug, Clone, Copy)]
pub enum Event {
    Quit,
    Debug,
    Reset,
    KeyDown(Key),
    KeyUp(Key)
}

pub trait Core {
    fn run<T: Platform>(&mut self, &mut T, bool);
    fn is_file(&str) -> bool;
    fn load_bios(&mut self, &str) -> bool;
    fn load_rom(&mut self, &str) -> bool;

    fn get_platform_parameters() -> (u32, u32, u32);
}

pub trait Platform {
    fn new(u32, u32, u32) -> Self;
    fn set_pixel(&mut self, u32, u32, Color);
    fn present(&mut self);

    fn set_title(&mut self, String);
    fn poll_event(&mut self) -> Option<Event>;
}
